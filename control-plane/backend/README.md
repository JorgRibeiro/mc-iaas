# MC-IaaS Control Plane — Backend

Este diretório contém o backend do Control Plane do MC-IaaS. Atualmente o projeto possui
a base da API, conexão assíncrona com PostgreSQL e os primeiros modelos persistentes do
domínio. Ainda não existem endpoints para cadastrar ou controlar Nodes e Instances.

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

Neste momento esses modelos e suas tabelas já existem, mas ainda não há services, repositories,
scheduler ou integração com os Compute Agents.

## Estrutura principal

```text
app/
├── main.py                  # cria e configura a aplicação FastAPI
├── api/
│   ├── router.py            # reúne as rotas HTTP
│   └── health.py            # implementa GET /health e GET /ready
├── core/
│   └── config.py            # carrega configurações do ambiente e do arquivo .env
├── db/
│   ├── base.py              # base declarativa, timestamps e convenções do SQLAlchemy
│   └── session.py           # engine, sessões assíncronas e teste de conexão com o banco
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

tests/                       # testes da configuração, saúde da API e metadata dos modelos
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
- `GET /ready`: confirma que a aplicação consegue acessar o PostgreSQL.

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
