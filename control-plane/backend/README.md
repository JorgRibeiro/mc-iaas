# MC-IaaS Control Plane — Backend

Este diretório contém o backend do Control Plane do MC-IaaS. Atualmente o projeto possui
a base da API, conexão assíncrona com PostgreSQL, modelos persistentes do domínio e
gerenciamento de Compute Nodes, polling e lifecycle assíncrono de Instances.

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

Compute Nodes possuem administração e observação automática. Instances possuem placement sticky,
lifecycle assíncrono e sincronização de estado observado. Operations são a fila durável do runner.
O refresh manual continua disponível. Reconciler e Activity/EventService ficam para 9.2.7.

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
├── workers/node_poller.py  # polling automático e backoff por Node
├── repositories/instance_repository.py # persistência de observações de Instances
├── services/node_observation_service.py # observação compartilhada e persistência
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
O mesmo serviço é usado pelo polling automático. O refresh pode ser usado para diagnóstico mesmo com `enabled=false`;
ele não habilita o Node; sincroniza também as Instances conhecidas, sem alterar desired_state.

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
  textos e chaves arbitrários de `errors` não são persistidos. Métricas não são sincronizadas.
- Falhas de credencial, transporte, autenticação ou protocolo: incrementam `consecutive_failures`,
  salvam uma mensagem fixa e preservam reachability, timestamps e o último estado observado.
  Ao atingir `NODE_OFFLINE_THRESHOLD`, o Node fica offline. O próximo sucesso completo limpa o erro.

Respostas: 200 para snapshot completo ou parcial; 404 para Node inexistente; 503 para credencial
indisponível, timeout ou falha de transporte; 502 para autenticação recusada pelo Agent (401/403),
status remoto malsucedido, JSON inválido ou contrato incompatível. Nenhum body de erro remoto é
exposto. A falha de observação é commitada antes de retornar 502/503, podendo ser consultada por GET.

Observações manuais e automáticas do mesmo Node são serializadas com `SELECT ... FOR UPDATE` para evitar perda de incrementos
e sobrescrita concorrente de observações. A transação mantém o lock durante a
chamada HTTP, limitada pelos timeouts configurados; outras escritas nesse Node podem aguardar.
Falhas de persistência causam rollback e não são disfarçadas como falhas do Agent.

Os testes usam HTTP simulado e sessões mockadas. O pytest básico não depende de JORGE, PostgreSQL,
túnel SSH ou token real. Não é necessário criar ou aplicar uma nova migration.

## Polling automático e Instances observadas (9.2.5)

Execute a V1 com **um único processo/worker Uvicorn**. O lifespan inicia uma task asyncio de
`NodePoller` após criar o cliente HTTP compartilhado. O primeiro ciclo começa no startup; não é
necessário chamar `/refresh`. No shutdown, a task é cancelada e aguardada; observações interrompidas
fazem rollback. Só depois o cliente HTTP é fechado e o engine PostgreSQL é descartado.

O poller busca apenas Nodes `enabled`, em ordem de nome, e observa cada um sequencialmente em sua
própria sessão/transação. Revalida `enabled` sob o lock para cobrir desabilitação após a descoberta.
Um erro em um Node não interrompe os demais; falhas de banco são registradas sem detalhes sensíveis
e o loop tenta novamente. O poller não faz chamadas de lifecycle; elas pertencem ao OperationRunner.

Configuração:

- `NODE_POLL_INTERVAL`: intervalo normal em segundos, positivo (padrão 10).
- `NODE_OFFLINE_THRESHOLD`: **contagem inteira de falhas consecutivas**, mínimo 1 (padrão 30,
  preservado da configuração anterior). Não é um timeout em segundos.
- `NODE_MAX_BACKOFF`: limite do backoff em segundos, positivo (padrão 300).

Após falhas, o atraso é `min(NODE_MAX_BACKOFF, NODE_POLL_INTERVAL * 2^(failures - 1))`.
Cada Node possui seu próximo horário em memória, baseado em relógio monotônico; um Node com falha
não impõe seu backoff aos demais. Os horários são reiniciados quando o processo reinicia. O loop
acorda no próximo horário devido ou no intervalo de descoberta, o que ocorrer primeiro. Como as
observações são sequenciais, chamadas lentas podem atrasar o ciclo. O refresh manual ignora a espera;
a próxima observação automática bem-sucedida retorna ao intervalo normal.

Falhas de transporte, timeout, credencial, autenticação ou protocolo contam para o threshold,
inclusive no refresh manual. Ao atingir o limite, muda apenas reachability para `offline`, além do
contador/erro. Saúde, capacidade, prontidão, `last_seen_at` e observações de Instances são preservadas.
Uma resposta válida, mesmo parcial, restaura `online` e zera falhas; um snapshot ainda parcial mantém
`last_error` sanitizado. Logs `node.online` e `node.offline` são emitidos somente na transição commitada.

A sincronização associa Instances pelo nome, apenas entre registros com `compute_node_id` igual ao
Node observado. Com uma seção `instances` presente e sem `errors["instances"]`:

- `running`, `stopped`, `paused`, `missing` e `unknown` são mapeados diretamente; `starting`,
  `stopping`, `error` e valores futuros viram `unknown` por não terem equivalente persistido.
- Runtime atualiza slot, IP e porta externa; runtime nulo limpa a alocação observada.
- Instance conhecida ausente vira `missing`, com runtime observado limpo e timestamp atualizado.
- `minecraft_status` só muda quando informado. O contrato real atual de `InstanceSummaryResponse`
  não traz esse campo; sua ausência preserva o valor anterior.
- `desired_state`, recursos configurados e erros de outras operações são preservados. Atualmente
  não se gravam erros de observação por Instance; sem proveniência, `last_error` não é apagado.

Uma seção nula/ausente, com erro parcial ou com nomes duplicados não modifica nenhuma observação
de Instance. Uma falha em `node_health` não impede sincronizar um inventário válido, e uma falha em
`instances` não impede atualizar saúde/capacidade. Node e Instances são commitados juntos.

Workloads sem Instance correspondente nesse Node geram `node.orphan_instance.detected` com id do
Node e contagem, sem copiar nomes arbitrários remotos para logs. Nenhuma Instance é criada/adotada
e nenhuma workload é removida. Events persistentes ficam para uma etapa posterior. A etapa 9.2.5 não adicionou endpoints de Instance ou migrations; os endpoints de lifecycle
são descritos abaixo em 9.2.6.

Validação manual: com o túnel disponível, inicie a API e consulte `GET /api/v1/nodes/{id}` após um
ciclo. Interrompa o túnel e acompanhe o contador até o threshold; considere o backoff ao aguardar.
Ao restaurar o túnel, a próxima tentativa automática deve recuperar `online`. Não é necessário
modificar o token nem chamar `/refresh`. Nos testes unitários, o poller do lifespan é substituído
por fake; o worker real é testado separadamente com sessões/HTTP simulados, sem acessar JORGE.

## Lifecycle distribuído de Instances (9.2.6)

A API persiste Instance/desired_state e uma Operation `pending` na mesma transação, retornando 202
com `operation_id`, `instance_id` e `status`. O runner consulta a fila a cada segundo quando ocioso,
reivindica com `FOR UPDATE SKIP LOCKED`, commita `in_progress` e só então faz HTTP. A conclusão da
Operation e a observação resultante da Instance são commitadas juntas.

| Endpoint | Resultado |
| --- | --- |
| `POST /api/v1/instances` | Enfileira CREATE; Scheduler seleciona o Node |
| `GET /api/v1/instances` | Lista Instances, sem tombstones |
| `GET /api/v1/instances/{id}` | Consulta uma Instance ativa |
| `POST /api/v1/instances/{id}/start` | Enfileira START de Instance stopped |
| `POST /api/v1/instances/{id}/stop` | Enfileira STOP de running/paused/stopped |
| `POST /api/v1/instances/{id}/restart` | Enfileira RESTART com observado e desejado running |
| `DELETE /api/v1/instances/{id}` | Enfileira DELETE somente de stopped |
| `GET /api/v1/operations/{id}` | Consulta resultado/progresso |
| `GET /api/v1/operations?instance_id=...` | Lista Operations da Instance, inclusive após DELETE |

UUID/payload inválido retorna 422; inexistente retorna 404; nome reservado, lifecycle inválido ou
Operation ativa retorna 409. Sem candidato para CREATE retorna 503. Node ocupado pelo lock pode
retornar 409 nas ações ou ser ignorado no placement; aguarde e repita a solicitação rejeitada.
As requisições não aguardam boot nem conclusão do HTTP do Agent.

Exemplo de CREATE (envie `accept_eula: true` somente após aceitar a EULA do Minecraft):

```json
{
  "name": "mc-test-01",
  "memory_mb": 2048,
  "vcpus": 1,
  "minecraft_version": "26.2",
  "vm_username": "operator",
  "accept_eula": true
}
```

O contrato real do Agent exige `vm_username` e aceite explícito da EULA. Os limites são memória
512..2048 MiB, exatamente 1 vCPU e nome alfanumérico/hífen/underscore de 3..50 caracteres iniciando
com alfanumérico. Usuários reservados são rejeitados. Não se aceitam passwords, credentials,
placement ou estados na entrada. Os parâmetros não secretos de CREATE são guardados no metadata
da Operation; esse metadata não é exposto na API de Operations.

**Placement:** Nodes devem estar enabled, online, ready e com `last_seen_at` e `last_observed_at`
recentes segundo `NODE_OBSERVATION_MAX_AGE` (padrão 60 segundos). Ranking: mais available_slots,
valores desconhecidos por último, desempate nome/id. CREATE aceita zero slots, pois cria stopped
sem runtime. O contrato observado não informa capacidade de RAM/disco para VMs stopped; não se
inventa reserva desses recursos. Os limites conhecidos do Agent são validados na entrada e ele
continua sendo autoridade final. START valida novamente o Node fixado, incluindo slots disponíveis,
tanto ao enfileirar quanto antes do dispatch. Não existe reagendamento ou failover.

**Semântica:** CREATE confirma stopped/runtime nulo. START confirma running e runtime disponível.
STOP é idempotente quando stopped e confirma runtime nulo. RESTART preserva desired=running, sem
retry automático. DELETE envia `delete_data=false`, sem STOP implícito; confirmação marca
observed=missing e `deleted_at`. Operations/Events e dados da VM são preservados. Nomes de tombstones
continuam reservados pelo índice global existente; não há reutilização automática.

**Erros e incerteza:** recusas explícitas 400/401/403/404/409/422 e pré-condições locais terminam
como failed. Timeout (inclusive 504 do Agent), falha de transporte, 5xx ou resposta incompatível
terminam como uncertain, pois podem ter ocorrido efeitos remotos. Desired_state é preservado.
Não há retry, adoção por nome ou resolução automática nesta etapa. Um CREATE failed bloqueia ações
subsequentes: uma workload homônima observada pelo poller não prova que foi criada pelo Control Plane.
`pending`, `in_progress` e `uncertain` bloqueiam segunda mutação via service e índice único PostgreSQL.

**Concorrência:** requisições usam locks não bloqueantes de Node; runner e poller serializam por
Node, com ordem de locks Node → Instance. O runner mantém o lock durante o HTTP para impedir que um
snapshot antigo sobrescreva a confirmação. CREATE/placement e Operation são atômicos. Violações
identificadas de `uq_instances_name` e `uq_operations_active_mutation_per_instance` viram conflito;
outros erros de banco não são escondidos como duplicidade.

**Startup/shutdown:** V1 usa um único processo/worker. O lifespan inicia HTTP, NodePoller e
OperationRunner; encerra/aguarda os workers antes de fechar HTTP e engine. Operations in_progress
abandonadas por processo anterior viram uncertain no startup, nunca pending. Cancelamento durante
dispatch tenta persistir uncertain; se o banco estiver indisponível, a recuperação ocorre no próximo
startup. Reconciler para resolver uncertain e display_state fica para 9.2.7.

**Credenciais geradas:** a senha de VM retornada pelo Agent no CREATE é descartada. Não há persistência,
log nem recuperação dessa senha pela Operation. Esta V1 não entrega credenciais de login da VM ao
usuário; o fluxo principal de lifecycle não depende delas. Bearer permanece no SecretProvider.

### Validação

Os unitários usam sessões/HTTP simulados e não iniciam workers reais no lifespan. A integração
PostgreSQL é opt-in, cria um schema temporário dentro de transação revertida e usa Agent simulado:

```bash
.venv/bin/python -m compileall app
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
RUN_POSTGRES_LIFECYCLE_TESTS=1 .venv/bin/python -m pytest tests/integration
.venv/bin/python -m alembic current
```

No teste manual com JORGE, aguarde cada Operation antes da próxima mutação. Sequência válida:
CREATE → START → STOP → START → RESTART → STOP → DELETE. RESTART exige running; DELETE exige stopped.
Não desligue o processo para repetir uma ação uncertain: ela permanece bloqueada para investigação
até a resolução apropriada. Nenhuma migration ou mudança no Compute Agent foi necessária.
