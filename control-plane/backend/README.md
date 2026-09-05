# MC-IaaS Control Plane — Backend

Este diretório contém o backend do Control Plane do MC-IaaS. Atualmente o projeto possui
a base da API, conexão assíncrona com PostgreSQL, modelos persistentes do domínio e
gerenciamento administrativo de Compute Nodes em `/api/v1/nodes`.

## O que acontece no código

A aplicação FastAPI recebe requisições HTTP e usa o SQLAlchemy assíncrono para acessar o
PostgreSQL. O Alembic controla a criação e a evolução das tabelas do banco.

Os quatro modelos atuais são:

- `ComputeNode`: representa uma máquina que executará as VMs e guarda sua última capacidade
  observada;
- `Instance`: representa um servidor Minecraft, separando o estado desejado pelo Control Plane
  do estado observado no Compute Agent;
- `Operation`: registra uma ação solicitada, como criar, iniciar, parar ou excluir uma Instance;
- `Event`: registra acontecimentos históricos da plataforma.

Compute Nodes possuem schemas, repository e service administrativos. Ainda não há scheduler,
polling periódico ou lifecycle de Instances. O refresh manual consulta o snapshot do Compute Agent.

## Estrutura principal

```text
app/
├── main.py                  # cria e configura a aplicação FastAPI
├── api/
│   ├── router.py            # reúne as rotas HTTP
│   ├── health.py            # implementa GET /health e GET /ready
│   └── nodes.py             # administração de Nodes e refresh manual
├── core/
│   └── config.py            # carrega configurações do ambiente e do arquivo .env
├── db/
│   ├── base.py              # base declarativa, timestamps e convenções do SQLAlchemy
│   └── session.py           # engine, sessões assíncronas e teste de conexão com o banco
├── clients/                # cliente HTTP do Agent e erros semânticos
├── secrets/                # resolução de tokens por referência
├── schemas/agent.py         # contrato mínimo de /node/snapshot
├── services/node_observation_service.py # observação manual e persistência
├── schemas/node.py         # entradas administrativas e resposta pública com capacity
├── repositories/node_repository.py # persistência de Nodes
├── services/node_service.py # regras, exceções de domínio e transações
└── models/
    ├── enums.py             # valores permitidos para estados, operações e eventos
    ├── types.py             # configuração comum dos enums no SQLAlchemy
    ├── compute_node.py      # modelo ComputeNode
    ├── instance.py          # modelo Instance
    ├── operation.py         # modelo Operation
    └── event.py             # modelo Event

migrations/
├── env.py                   # conecta o Alembic ao metadata dos modelos
└── versions/                # migrations versionadas do PostgreSQL

tests/                       # testes unitários de configuração, modelos, Nodes e API
compose.yml                  # PostgreSQL local para desenvolvimento
alembic.ini                  # configuração do Alembic
pyproject.toml               # dependências e configuração das ferramentas Python
.env.example                 # exemplo das variáveis de ambiente necessárias
```

## Como executar

Requer Python 3.12 ou superior e Docker Compose.

```bash
cp .env.example .env
docker compose up -d
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Endpoints disponíveis:

- `GET /health`: confirma que a aplicação está em execução sem depender do banco;
- `GET /ready`: confirma que a aplicação consegue acessar o PostgreSQL;
- `POST /api/v1/nodes`: cadastra um Node (201);
- `GET /api/v1/nodes`: lista Nodes ordenados por nome (200);
- `GET /api/v1/nodes/{node_id}`: consulta um Node (200);
- `PATCH /api/v1/nodes/{node_id}`: altera parcialmente um Node (200).

UUID ou payload inválido retorna 422; Node inexistente retorna 404; nome duplicado retorna 409.
Não há DELETE. Os endpoints de infraestrutura permanecem sem prefixo.

## Banco de dados e migrations

O PostgreSQL é obrigatório. Para aplicar as migrations e consultar a versão atual do schema:

```bash
alembic upgrade head
alembic current
```

A migration atual cria as tabelas `compute_nodes`, `instances`, `operations` e `events`, seus
enums, relacionamentos, checks e índices. Alterações futuras no schema devem ser feitas por novas
migrations; a aplicação não usa `create_all()`.

## Verificações de qualidade

Com o ambiente virtual ativado:

```bash
.venv/bin/python -m compileall app
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
```

## Cadastro manual de um Compute Node

Depois de iniciar a API e aplicar a migration existente, o cadastro de JORGE pode ser feito
manualmente (nenhum Node é criado por seed ou startup):

```bash
curl -X POST http://127.0.0.1:8001/api/v1/nodes \
  -H 'Content-Type: application/json' \
  -d '{"name":"JORGE","endpoint":"http://127.0.0.1:8000","credential_ref":"jorge-agent","enabled":true}'

curl http://127.0.0.1:8001/api/v1/nodes
```

O cadastro apenas armazena o endpoint, sem tentativa de conexão. O refresh manual usa esse endereço
para acessar o Agent; no exemplo local, o caminho é o túnel SSH. `credential_ref` armazena apenas uma referência, nunca o segredo,
e é omitido da resposta pública. URLs aceitam HTTP/HTTPS e têm barras finais removidas;
credenciais na URL, query strings e fragments são rejeitados.

POST e PATCH aceitam somente `name`, `endpoint`, `credential_ref` e `enabled`. PATCH distingue
campos omitidos de valores explícitos: `null` é rejeitado, `{}` mantém os dados existentes.
Campos observados são rejeitados na entrada. A resposta agrupa os quatro campos de capacidade
em `capacity`; os valores permanecem desconhecidos até uma observação válida do Agent.
Desabilitar um Node apenas o torna inelegível para uso futuro pelo scheduler, sem alterar sua saúde.

O repository executa `flush` nas escritas; o service controla `commit` e `rollback`. Leituras
não fazem commit. Cada requisição usa uma sessão do engine compartilhado. A verificação prévia
de nome é complementada pelo índice único existente: violações PostgreSQL `23505` identificadas
como `uq_compute_nodes_name` viram conflito, inclusive em races; outros erros são propagados.

Os testes de Nodes usam mocks, sem SQLite e sem depender do container PostgreSQL.

## Refresh manual do estado observado (9.2.4)

`POST /api/v1/nodes/{node_id}/refresh` consulta imediatamente `GET /node/snapshot` no endpoint
persistido do Node, salva a observação e retorna a mesma representação pública usada pelo GET.
Não existe loop de polling. O refresh pode ser usado para diagnóstico mesmo com `enabled=false`;
ele não habilita o Node nem altera Instances ou Events.

O `EnvironmentSecretProvider` transforma referências contendo letras ASCII, dígitos, hífen e
underscore em `MC_IAAS_AGENT_TOKEN_` + referência em maiúsculas, trocando hífens por underscores.
Por exemplo, `jorge-agent` resolve `MC_IAAS_AGENT_TOKEN_JORGE_AGENT`. Maiúsculas/minúsculas e
hífens/underscores são equivalentes nessa estratégia; use referências distintas após normalização.
Outros caracteres são rejeitados pelo provider. O ambiente do processo tem precedência sobre o
`.env` local, inclusive quando seu valor está vazio. Não há interpolação de variáveis no token.
O `.env` é lido no startup: reinicie a API depois de alterar o token.

Coloque o token real somente no `.env` local, na variável indicada no `.env.example`, ou no ambiente
do processo. O valor não é persistido, retornado nem registrado em logs. Não envie token à API do
Control Plane: ela resolve a referência internamente. Credencial ausente, vazia ou incompatível com
um header produz erro semântico sanitizado.

Com a API iniciada a partir de `control-plane/backend`, usando o ambiente correto:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Em outro terminal, substitua o UUID pelo id retornado no cadastro:

```bash
NODE_ID="UUID-DO-NODE"
curl -X POST "http://127.0.0.1:8001/api/v1/nodes/${NODE_ID}/refresh"
curl "http://127.0.0.1:8001/api/v1/nodes/${NODE_ID}"
```

O lifespan cria e fecha um único `httpx.AsyncClient`, compartilhado por todos os Nodes, com
`AGENT_CONNECT_TIMEOUT` e `AGENT_READ_TIMEOUT`. Cada chamada envia seu próprio header Bearer.
Redirecionamentos e proxies herdados do ambiente estão desativados. Endereços vêm do banco.

- Snapshot válido: `online`, `last_seen_at` atualizado, falhas zeradas e versão atualizada.
  Com `node_health` disponível, saúde, prontidão e capacidade são atualizadas; `last_observed_at`
  usa a hora UTC local de recebimento, evitando depender do relógio do Agent.
- Snapshot parcial: mantém `online`. Sem `node_health`, preserva saúde, prontidão, capacidade e
  `last_observed_at` anteriores. Erros parciais geram apenas `Partial Agent snapshot` em `last_error`;
  textos e chaves arbitrários de `errors` não são persistidos. Métricas e Instances não são sincronizadas.
- Falhas de credencial, transporte, autenticação ou protocolo: incrementam `consecutive_failures`,
  salvam uma mensagem fixa e preservam reachability, timestamps e o último estado observado.
  Não existe transição automática para offline nesta etapa. O próximo sucesso completo limpa o erro.

Respostas: 200 para snapshot completo ou parcial; 404 para Node inexistente; 503 para credencial
indisponível, timeout ou falha de transporte; 502 para autenticação recusada pelo Agent (401/403),
status remoto malsucedido, JSON inválido ou contrato incompatível. Nenhum body de erro remoto é
exposto. A falha de observação é commitada antes de retornar 502/503, podendo ser consultada por GET.

Refreshes do mesmo Node são serializados com `SELECT ... FOR UPDATE` para evitar perda de incrementos
e sobrescrita concorrente de observações. Nesta operação manual, a transação mantém o lock durante a
chamada HTTP, limitada pelos timeouts configurados; outras escritas nesse Node podem aguardar.
Falhas de persistência causam rollback e não são disfarçadas como falhas do Agent.

Os testes usam HTTP simulado e sessões mockadas. O pytest básico não depende de JORGE, PostgreSQL,
túnel SSH ou token real. Não é necessário criar ou aplicar uma nova migration.
