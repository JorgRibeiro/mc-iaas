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
polling, integração com Compute Agents ou lifecycle de Instances.

## Estrutura principal

```text
app/
├── main.py                  # cria e configura a aplicação FastAPI
├── api/
│   ├── router.py            # reúne as rotas HTTP
│   ├── health.py            # implementa GET /health e GET /ready
│   └── nodes.py             # cadastro, consulta e atualização administrativa de Nodes
├── core/
│   └── config.py            # carrega configurações do ambiente e do arquivo .env
├── db/
│   ├── base.py              # base declarativa, timestamps e convenções do SQLAlchemy
│   └── session.py           # engine, sessões assíncronas e teste de conexão com o banco
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
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
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
python -m compileall app
ruff check .
pytest
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

O endpoint do Agent é somente armazenado, sem tentativa de conexão. Nesse exemplo, será acessado
futuramente pelo túnel SSH. `credential_ref` armazena apenas uma referência, nunca o segredo,
e é omitido da resposta pública. URLs aceitam HTTP/HTTPS e têm barras finais removidas;
credenciais na URL, query strings e fragments são rejeitados.

POST e PATCH aceitam somente `name`, `endpoint`, `credential_ref` e `enabled`. PATCH distingue
campos omitidos de valores explícitos: `null` é rejeitado, `{}` mantém os dados existentes.
Campos observados são rejeitados na entrada. A resposta agrupa os quatro campos de capacidade
em `capacity`; os valores permanecem desconhecidos até uma futura observação do Agent.
Desabilitar um Node apenas o torna inelegível para uso futuro pelo scheduler, sem alterar sua saúde.

O repository executa `flush` nas escritas; o service controla `commit` e `rollback`. Leituras
não fazem commit. Cada requisição usa uma sessão do engine compartilhado. A verificação prévia
de nome é complementada pelo índice único existente: violações PostgreSQL `23505` identificadas
como `uq_compute_nodes_name` viram conflito, inclusive em races; outros erros são propagados.

Os testes de Nodes usam mocks, sem SQLite e sem depender do container PostgreSQL.
