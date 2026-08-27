# MC-IaaS Compute Agent

O `jorge-agent` é o daemon/API local do Compute Node do MC-IaaS. Ele converte operações sobre instâncias Minecraft em mudanças no libvirt/KVM, storage, rede e filesystem do host.

Este documento descreve o componente implementado. Para a visão geral do projeto, consulte o [README principal](../README.md).

## Sumário

- [1. Visão geral](#1-visão-geral)
- [2. Arquitetura](#2-arquitetura)
- [3. Modelo de instância](#3-modelo-de-instância)
- [4. Runtime e rede](#4-runtime-e-rede)
- [5. Storage e persistência](#5-storage-e-persistência)
- [6. Concorrência e invariantes](#6-concorrência-e-invariantes)
- [7. Quotas e validação](#7-quotas-e-validação)
- [8. Segurança](#8-segurança)
- [9. Observabilidade](#9-observabilidade)
- [10. Recovery e reconciliação](#10-recovery-e-reconciliação)
- [11. API Reference](#11-api-reference)
- [12. Instalação e operação](#12-instalação-e-operação)
- [13. Testes](#13-testes)
- [14. Limitações e roadmap](#14-limitações-e-roadmap)

## 1. Visão geral

Na arquitetura pretendida, o Control Plane envia operações de alto nível ao Compute Agent de um nó. O agente aplica essas operações localmente e devolve estado, capacidade e observabilidade. O Control Plane ainda não está implementado neste repositório; hoje a API é consumida localmente ou por túnel SSH.

Responsabilidades do Compute Agent:

- criar, consultar e remover domínios libvirt;
- orquestrar `CREATE`, `START`, `STOP`, `RESTART` e `DELETE`;
- criar discos, volumes persistentes e seeds cloud-init;
- alocar e liberar NIC, IP, DHCP e port-forward;
- impor quotas e serializar operações concorrentes;
- inicializar Minecraft e acessar RCON internamente;
- expor health, métricas, consoles, snapshot e reconciliação;
- verificar invariantes e desfazer operações incompletas.

## 2. Arquitetura

```text
Control Plane (futuro)
        ↓ HTTP/WebSocket autenticado
Compute Agent (FastAPI)
        ↓
libvirt → KVM/QEMU
        ↓
VM Minecraft
```

As principais camadas são:

| Camada | Responsabilidade |
|---|---|
| API | Rotas HTTP/WebSocket, autenticação, schemas e códigos de resposta |
| Orquestração | Lifecycle da instância, ordem das operações e rollback |
| Virtualização | Definição, estado, boot, shutdown, reboot e console libvirt |
| Runtime/rede | Slots, NIC, MAC, DHCP, leases, port-forward e firewall |
| Storage/provisionamento | Imagem base, overlays, volume de dados e cloud-init |
| Minecraft | Bootstrap, health TCP, comandos e console RCON |
| Persistência local | Metadata e secrets por instância |
| Observabilidade/recovery | Health, métricas, invariantes, snapshot e reconciliação |

`main.py` é a borda da aplicação. `instance_service.py` coordena as mutações; os demais services encapsulam as operações de infraestrutura.

## 3. Modelo de instância

Recursos persistentes e runtime possuem ciclos de vida separados:

```text
CREATE
  ↓ cria recursos persistentes; runtime = null
STOPPED ── START ──→ RUNNING
   ↑                   │
   └────── STOP ───────┘
                       ↺ RESTART

STOPPED ── DELETE ──→ removida
```

| Operação | Comportamento |
|---|---|
| `CREATE` | Cria storage, secret RCON, cloud-init, domínio e metadata. Retorna `stopped` sem slot, IP ou porta. |
| `START` | Aloca runtime, anexa a NIC, configura DHCP/forward e inicia o domínio. |
| `STOP` | Solicita shutdown gracioso, aguarda até 60 s e libera todo o runtime. É idempotente para domínio já parado. |
| `RESTART` | Reinicia uma VM ativa e preserva o runtime existente. |
| `DELETE` | Exige domínio parado. Remove domínio, cloud-init, secrets e disco de sistema; preserva o volume de dados por padrão. |

Estados expostos pelo schema:

| Estado | Significado |
|---|---|
| `stopped` | Domínio desligado; no estado consistente, não possui runtime. |
| `running` | Domínio ativo (`running` ou `blocked` no libvirt). |
| `paused` | Domínio pausado ou suspenso; conta como instância ativa. |
| `starting` | Declarado no enum público; o mapeamento libvirt atual não o emite. |
| `stopping` | Libvirt reporta shutdown em andamento. |
| `error` | Domínio em estado crashed. |
| `unknown` | Estado libvirt sem mapeamento conhecido. |

Conflitos de lifecycle retornam `409`: `CREATE` duplicado, `START` de domínio ativo, `RESTART` sem runtime ou em domínio parado e `DELETE` de domínio ativo. Operações sobre nome inexistente retornam `404`.

No `DELETE`, o query parameter `delete_data` é `false` por padrão:

- `delete_data=false`: mantém o volume RAW e marca a metadata como deletada/preservada;
- `delete_data=true`: remove também volume e metadata.

Ainda não existe uma operação de restore para um volume preservado.

## 4. Runtime e rede

Runtime é a combinação de slot, IP interno e porta externa. Ele só existe enquanto uma instância está ativa.

| Slot | IP da VM | Porta externa | Destino Minecraft |
|---:|---|---:|---:|
| 1 | `10.50.0.10` | `25565` | `10.50.0.10:25565` |
| 2 | `10.50.0.11` | `25566` | `10.50.0.11:25565` |
| 3 | `10.50.0.12` | `25567` | `10.50.0.12:25565` |
| 4 | `10.50.0.13` | `25568` | `10.50.0.13:25565` |

| Serviço | Porta interna | Exposição |
|---|---:|---|
| Minecraft | `25565/TCP` | Publicada pela porta externa do slot |
| RCON | `25575/TCP` | Somente entre o agente e a VM; nunca encaminhada publicamente |

O agente usa a rede libvirt `mc-net`, que deve existir e ser compatível com os quatro IPs estáticos. A alocação seleciona o primeiro slot cujo IP não esteja reservado nem alugado e cuja porta externa não esteja publicada.

No `START`, o agente:

1. deriva uma MAC determinística do nome (`52:54:00` + 3 bytes de SHA-256);
2. anexa uma interface VirtIO ao domínio persistente;
3. cria uma reserva DHCP live e persistente;
4. grava o forward `porta_externa IP 25565`;
5. reaplica o firewall;
6. inicia a VM.

No `STOP`, o processo inverso libera lease, reserva DHCP, port-forward e NIC. O helper `/srv/mc-iaas/scripts/release-dhcp-lease.sh` e o aplicador `/srv/mc-iaas/scripts/apply-firewall.sh` são dependências do host.

## 5. Storage e persistência

```text
base QCOW2 somente leitura
    └── overlay QCOW2 por VM (sistema)

volume RAW por VM (dados Minecraft)
    └── /srv/minecraft dentro da VM
```

| Recurso | Implementação | Tamanho/lifecycle |
|---|---|---|
| Imagem base | Ubuntu 24.04 Minimal QCOW2, backing store imutável | Compartilhada; deve existir e não possuir bits de escrita |
| Disco de sistema | Overlay `{name}.qcow2` no pool `mc-instances` | 10 GiB; removido no `DELETE` |
| Volume de dados | `{name}-data.raw` no pool `mc-volumes` | 5 GiB, sparse; preservado por padrão no `DELETE` |
| Seed cloud-init | `seed.img` RAW, NoCloud, somente leitura na VM | Criado no `CREATE`; removido no `DELETE` |

O pool `mc-images` é ativado pelos scripts; o código lê a imagem base pelo caminho configurado. Os backing paths dos pools `mc-instances` e `mc-volumes` pertencem à configuração libvirt do host e não são fixados pelo Python.

Dentro da VM, cloud-init:

- cria o usuário solicitado com senha hash e root desabilitado;
- instala OpenJDK 25 e `curl`;
- cria o usuário/grupo `minecraft` com UID/GID 2000;
- formata `vdc` em ext4 quando necessário e monta em `/srv/minecraft`;
- baixa e valida o JAR pelo SHA-1 fixado no catálogo;
- configura EULA, RCON e `minecraft.service`.

O catálogo atual contém somente Minecraft `26.2`.

### Diretórios importantes

| Caminho | Conteúdo |
|---|---|
| `/srv/mc-iaas/storage/images/ubuntu-24.04-minimal-base.qcow2` | Imagem base |
| `/srv/mc-iaas/cloud-init/{name}/` | `user-data`, `meta-data` e `seed.img` |
| `/srv/mc-iaas/metadata/{name}.json` | Configuração persistente e marcadores de deleção |
| `/srv/mc-iaas/secrets/{name}.json` | Senha RCON da instância |
| `/srv/mc-iaas/secrets/agent-api-token` | Bearer token administrativo |
| `/srv/mc-iaas/config/port-forwards.conf` | Estado desejado dos forwards Minecraft |
| `/srv/mc-iaas/scripts/` | Helpers de firewall e DHCP |
| `/srv/mc-iaas/logs/jorge-agent.log` | stdout/stderr do launcher |
| `/srv/mc-iaas/run/jorge-agent.pid` | PID gravado pelo launcher |
| `/srv/mc-iaas/run/locks/` | Locks de instância e runtime |

Os arquivos de secret por instância são criados com modo `0600` em diretório `0700`. O `user-data` também é restrito a `0600`, pois contém material sensível usado no primeiro boot.

## 6. Concorrência e invariantes

### Locks

Os locks usam `fcntl.flock()` em arquivos, portanto serializam processos distintos, não apenas threads do Uvicorn.

| Lock | Escopo | Operações |
|---|---|---|
| Instância | `/srv/mc-iaas/run/locks/instances/{name}.lock` | `CREATE`, `START`, `STOP`, `RESTART`, `DELETE` e reconciliation da instância |
| Runtime global | `/srv/mc-iaas/run/locks/runtime.lock` | Alocação/liberação de slot, NIC, DHCP, forward e firewall |

Quando ambos são necessários, a ordem obrigatória é:

```text
instance lock → runtime lock
```

O lock de instância permanece durante toda a mutação. O lock global é mantido apenas durante a mudança do runtime, evitando bloquear outras VMs durante boot, shutdown ou reboot.

O `START` trata a preparação como uma unidade: se NIC, DHCP, port-forward ou firewall falhar, tenta desfazer em ordem inversa o que já foi aplicado. Se o boot do domínio falhar depois da preparação, libera o runtime. A liberação explícita agrega falhas em `RuntimeCleanupError`; se o próprio rollback falhar, a operação também falha e invariantes/recovery devem detectar o resíduo. Uma resposta de sucesso nunca é emitida para uma preparação incompleta.

### Invariantes de projeto

| Invariante | Consequência |
|---|---|
| Um slot/IP/porta não pertence a dois runtimes | Alocação global serializada e disponibilidade derivada do estado real |
| No máximo quatro workloads ativos via API | O quinto `START` falha por ausência de slot |
| `CREATE` não aloca runtime | Instância recém-criada retorna `runtime: null` |
| VM ativa possui runtime | Ausência é crítica; não se reconstrói automaticamente |
| VM parada não possui runtime | Resíduo pode ser liberado pela reconciliação |
| `STOP` libera runtime | NIC, DHCP, lease e forward são removidos após o shutdown |
| `RESTART` mantém runtime | O domínio é reiniciado sem desalocação |
| `DELETE` exige VM parada | A remoção não executa um `STOP` implícito |
| RCON não é público | Forward com destino `25575` é uma violação crítica |
| Imagem base é imutável | Ausência ou permissão de escrita é uma violação crítica |

As verificações atuais também cobrem atividade/existência de `mc-net`, pools `mc-instances` e `mc-volumes`, scripts obrigatórios, metadata gerenciada e relação domínio/runtime. Metadata de volume preservado, marcada como deletada, é ignorada na verificação de domínio.

## 7. Quotas e validação

| Recurso | Mínimo | Padrão | Máximo |
|---|---:|---:|---:|
| Memória | 512 MiB | 2048 MiB | 2048 MiB |
| vCPU | 1 | 1 | 1 |
| Workloads ativos | — | — | 4 slots |
| Disco de sistema | — | 10 GiB | 10 GiB |
| Volume de dados | — | 5 GiB | 5 GiB |

O schema de `CREATE` também exige:

- `name`: 3–50 caracteres, começa com alfanumérico e usa apenas letras, números, `_` ou `-`;
- `vm_username`: 1–32 caracteres no formato Linux aceito; `root`, `minecraft` e `libvirt-qemu` são reservados;
- `vm_password`: opcional, mínimo de 12 caracteres quando fornecido;
- `minecraft_version`: somente `26.2` é suportada pelo catálogo atual;
- `accept_eula=true`: aceitação explícita obrigatória.

Se `vm_password` for omitida, o agente gera uma senha e a devolve apenas no campo `generated_password` da resposta de criação. Violações de schema geram `422`; EULA recusada ou versão sem suporte geram `400`.

## 8. Segurança

A API administrativa usa um Bearer token compartilhado. Não existem login de usuário, sessão, JWT ou OAuth no Compute Agent.

```http
Authorization: Bearer <agent-api-token>
```

- O token é lido de `/srv/mc-iaas/secrets/agent-api-token` a cada validação.
- Token ausente, header malformado ou token inválido retorna `401`.
- Secret ausente ou vazio torna a autenticação indisponível e retorna `503`.
- A comparação usa `secrets.compare_digest()`.
- HTTP administrativo e ambos os WebSockets exigem o mesmo header.
- `/health` é público e retorna somente `status` e `service`.
- `/docs`, `/redoc` e `/openapi.json` estão desabilitados.
- O launcher faz bind somente em `127.0.0.1:8000`.
- Acesso remoto de desenvolvimento deve usar SSH local forwarding; o canal permanente com o futuro Control Plane ainda não foi definido.
- Tokens nunca devem ser enviados em query string.
- RCON `25575` nunca deve ser publicado; o agente acessa a VM pela rede interna.

Não registrar nem copiar para documentação: API token, header `Authorization`, senha da VM, senha gerada, senha RCON, conteúdo de secrets, payload completo de `CREATE` ou comandos RCON completos.

O log também é dado operacional sensível e deve possuir permissões restritas no host. O código Python usa um `StreamHandler` para stdout; `start.sh` redireciona stdout/stderr para `/srv/mc-iaas/logs/jorge-agent.log`. Não há `FileHandler` nem rotação de logs implementados no agente.

Exemplo de túnel SSH:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@compute-node
```

## 9. Observabilidade

### Agent status

`GET /agent/status` informa `status` (`running`), `service`, `version`, `started_at` em UTC e `uptime_seconds`, calculado com relógio monotônico.

### Node health e readiness

`GET /node/health` agrega `libvirt`, `network`, `storage`, `invariants` e capacidade.

| Campo | Semântica |
|---|---|
| `status` | `healthy`, `degraded` ou `unhealthy` |
| `ready` | Indica se o nó pode anunciar capacidade ao scheduler |
| `max_active_instances` | Capacidade estrutural: 4 |
| `active_instances` | Contagem real de domínios `running` ou `paused` |
| `occupied_runtime_slots` | Slots fisicamente ocupados, derivados de IPs/leases/forwards |
| `available_slots` | Capacidade anunciável; vira `0` quando `ready=false` |

`active_instances` e `occupied_runtime_slots` medem coisas diferentes. Não se deve inferir uma pela outra. Um nó inconsistente pode possuir slots fisicamente livres e ainda anunciar `available_slots: 0`.

O modelo de invariantes aceita severidades `warning` e `critical`:

- `critical` produz `unhealthy` e `ready=false`;
- somente `warning` produziria `degraded` sem necessariamente retirar readiness.

As verificações atualmente cadastradas usam a severidade padrão `critical`; portanto, o contrato suporta warnings/degraded, mas ainda não há uma verificação que emita warning.

### Métricas do host

`GET /node/metrics` usa standard library e procfs, sem `psutil`:

| Grupo | Campos |
|---|---|
| CPU | `usage_percent` (amostra de 0,5 s), `load_1m`, `load_5m`, `load_15m` |
| Memória | `total_bytes`, `used_bytes`, `available_bytes`, `usage_percent` |
| `root_disk` | `path`, `total_bytes`, `used_bytes`, `free_bytes`, `usage_percent` para `/` |
| `mc_iaas_disk` | Mesmos campos para `/srv/mc-iaas` |

### Health e métricas da instância

`GET /instances/{name}/health` separa estado do domínio e disponibilidade do Minecraft:

| `minecraft_state` | Condição |
|---|---|
| `stopped` | Domínio inativo; `runtime` é `null` |
| `unavailable` | Domínio ativo sem runtime ou TCP `25565` ainda inacessível |
| `online` | Domínio ativo, runtime presente e TCP `25565` acessível |

É normal observar `instance_state: running` e `minecraft_state: unavailable` durante o boot. O probe usa conexão TCP com timeout de 1 s e não comprova readiness do RCON.

`GET /instances/{name}/metrics` expõe somente:

| Grupo | Campos |
|---|---|
| CPU | `usage_percent`, `cpu_time_seconds`, `vcpus` |
| Memória | `configured_mb`, `current_mb`, `rss_mb` |
| Storage | `system` e `data`, cada um com `capacity_bytes` e `allocation_bytes` |
| Rede | `rx_bytes`, `tx_bytes` |

Alguns campos são anuláveis: CPU instantânea para VM não running, RSS sem estatística disponível, volumes ausentes e rede de domínio inativo/sem interface.

### Node snapshot

`GET /node/snapshot` é a fotografia agregada do Compute Node e a principal interface de observabilidade projetada para consumo pelo futuro Control Plane.

```text
generated_at
agent
node_health | null
node_metrics | null
instances   | null
errors      { seção: mensagem }
```

A coleta é parcialmente tolerante a falhas. `agent` e `generated_at` sempre compõem a resposta; falhas isoladas em health, métricas ou inventário tornam somente a seção correspondente `null` e são registradas em `errors`.

### Logging operacional

Cada linha contém timestamp UTC, nível, logger e mensagem. Os eventos operacionais estruturados acrescentam `event=...`:

```text
timestamp UTC level logger event=...
```

As famílias atuais incluem `instance.create.*`, `instance.start.*`, `instance.stop.*`, `instance.restart.*`, `instance.delete.*`, `auth.*` e `recovery.*`. São registrados pedidos, rejeições, conclusão, rollback e tipo de erro, sem material secreto.

## 10. Recovery e reconciliação

A reconciliação executa automaticamente no startup e pode ser solicitada por `POST /node/reconcile`. Ela usa os mesmos locks do lifecycle, sempre na ordem `instance → runtime`, e revalida o estado do domínio dentro do lock.

| Estado observado | Ação conservadora |
|---|---|
| VM parada + runtime residual | Libera lease, DHCP, forward e NIC; inclui o nome em `recovered` |
| VM parada + sem runtime | Mantém; inclui em `unchanged` |
| VM ativa + runtime | Mantém; inclui em `unchanged` |
| VM ativa + sem runtime | Não reconstrói automaticamente; mantém e deixa a invariante detectar |
| Metadata sem nome, marcada como deletada ou sem domínio | Ignora; não executa remoção arbitrária |
| Falha por instância | Registra em `errors` |

No startup, qualquer erro de recovery aborta a inicialização. Em seguida, as invariantes são verificadas; ocorrência crítica também impede a API de iniciar. O endpoint manual retorna `healthy: false` quando o relatório contém erros.

## 11. API Reference

Base local: `http://127.0.0.1:8000`.

| Método | Endpoint | Auth | Finalidade |
|---|---|---|---|
| `GET` | `/health` | Pública | Liveness minimalista do processo |
| `GET` | `/agent/status` | Bearer | Versão, início e uptime do agente |
| `GET` | `/hypervisor/health` | Bearer | URI, host, versão e contagens do libvirt |
| `GET` | `/node/health` | Bearer | Health, readiness, invariantes e capacidade do nó |
| `GET` | `/node/metrics` | Bearer | CPU, memória e discos do host |
| `GET` | `/node/snapshot` | Bearer | Snapshot agregado e tolerante a falhas parciais |
| `POST` | `/node/reconcile` | Bearer | Reconcilia runtimes residuais seguros |
| `GET` | `/instances` | Bearer | Lista domínios gerenciados |
| `POST` | `/instances` | Bearer | Cria uma instância parada |
| `GET` | `/instances/{name}` | Bearer | Detalha uma instância |
| `POST` | `/instances/{name}/start` | Bearer | Aloca runtime e inicia |
| `POST` | `/instances/{name}/stop` | Bearer | Para e libera runtime |
| `POST` | `/instances/{name}/restart` | Bearer | Reinicia preservando runtime |
| `DELETE` | `/instances/{name}` | Bearer | Remove instância parada; query `delete_data=false` |
| `GET` | `/instances/{name}/health` | Bearer | Estado da VM e disponibilidade Minecraft |
| `GET` | `/instances/{name}/metrics` | Bearer | Métricas da VM |
| `POST` | `/instances/{name}/minecraft/command` | Bearer | Executa um comando RCON |
| `WS` | `/instances/{name}/console` | Bearer no handshake | Console serial bidirecional da VM |
| `WS` | `/instances/{name}/minecraft/console` | Bearer no handshake | Console Minecraft por comandos RCON |

### Requests principais

Carregue o token sem imprimi-lo:

```bash
TOKEN="$(< /srv/mc-iaas/secrets/agent-api-token)"
AUTH=(-H "Authorization: Bearer $TOKEN")
```

Criar uma instância (a resposta é `201` e permanece sem runtime):

```bash
curl -fsS "${AUTH[@]}" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "survival-01",
    "vm_username": "adminmc",
    "memory_mb": 2048,
    "vcpus": 1,
    "minecraft_version": "26.2",
    "accept_eula": true
  }' \
  http://127.0.0.1:8000/instances
```

As ações de lifecycle não possuem body:

```bash
curl -fsS "${AUTH[@]}" -X POST \
  http://127.0.0.1:8000/instances/survival-01/start
```

Executar RCON:

```bash
curl -fsS "${AUTH[@]}" \
  -H 'Content-Type: application/json' \
  -d '{"command":"list"}' \
  http://127.0.0.1:8000/instances/survival-01/minecraft/command
```

Ao terminar, remova a variável local:

```bash
unset TOKEN AUTH
```

### Respostas e erros

| Código | Uso atual |
|---:|---|
| `200` | Consultas, ações, delete, RCON e reconciliation bem-sucedidos |
| `201` | Instância criada |
| `400` | Regra de criação inválida após validação do schema, como EULA recusada ou versão sem suporte |
| `401` | Bearer token ausente, malformado ou inválido |
| `404` | Instância ou secret associado não encontrado |
| `409` | Conflito de lifecycle, runtime/quota sem slot ou erro de protocolo/autenticação RCON |
| `422` | Payload ou parâmetros rejeitados pela validação FastAPI/Pydantic |
| `500` | Falha interna não classificada na operação |
| `503` | Componente necessário indisponível: autenticação, libvirt, coleta do nó ou RCON |
| `504` | Timeout no shutdown durante `STOP` ou `DELETE` |

Erros HTTP usam o formato padrão `{"detail": "..."}`. Um `/node/health` não ready pode responder `200` com `ready: false`; `503` indica que a avaliação em si não pôde ser concluída.

Nos WebSockets, autenticação inválida é rejeitada antes de `websocket.accept()`, sem abrir o console. Depois do handshake, o console serial usa `4404` para instância ausente, `4409` para conflito de estado e `1011` para erro interno.

## 12. Instalação e operação

### Pré-requisitos

- Linux com KVM/QEMU e libvirt (`qemu:///system`);
- Python 3.11 ou superior;
- `cloud-localds`;
- rede libvirt `mc-net` e pools `mc-images`, `mc-instances`, `mc-volumes` configurados;
- imagem base no caminho documentado;
- scripts de firewall e liberação DHCP instalados em `/srv/mc-iaas/scripts/`;
- `sudo -n` autorizado para os helpers necessários;
- token não vazio em `/srv/mc-iaas/secrets/agent-api-token`, fora do Git e preferencialmente com modo `0600`.

### Ambiente Python

Na pasta `compute-agent/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[compute,dev]'
```

O extra `compute` instala `libvirt-python`; `dev` instala `pytest` e `httpx`.

### Scripts

```bash
./start.sh       # prepara rede/pools/firewall e inicia o agente
./stop.sh        # para somente o processo do agente
./stop-final.sh  # para VMs, valida invariantes e desativa a infraestrutura
```

`start.sh` ativa `mc-net` e os três pools, aplica o firewall, inicia Uvicorn via `nohup`, grava o PID e aguarda `/health`. O bind é `127.0.0.1:8000` e o output vai para `/srv/mc-iaas/logs/jorge-agent.log`.

`stop.sh` tenta `SIGTERM`, usa o PID file ou procura o Uvicorn como fallback e envia `SIGKILL` após 10 s. Não para VMs, rede nem pools.

`stop-final.sh` garante que o agente esteja disponível, para graciosamente todas as VMs, verifica invariantes, para o processo e desativa rede/pools. Ele autentica suas chamadas administrativas com o token local e preserva os dados. Não equivale a `DELETE`.

Também é possível iniciar diretamente no Compute Node:

```bash
.venv/bin/python -m uvicorn \
  jorge_agent.main:app \
  --host 127.0.0.1 \
  --port 8000
```

Probe local:

```bash
curl -fsS http://127.0.0.1:8000/health
```

Não há unit systemd versionada; o gerenciamento atual usa scripts, `nohup`, log e PID file.

## 13. Testes

A suíte E2E percorre o lifecycle real: `CREATE`, consultas, `START`, readiness Minecraft/RCON, métricas, `RESTART`, `STOP`, segundo ciclo, `DELETE` destrutivo, artefatos e invariantes finais.

Ela cria VMs, volumes e regras de rede reais. Por segurança, é ignorada sem opt-in:

```bash
MC_IAAS_RUN_E2E=1 \
.venv/bin/python -m pytest -v -s -m e2e tests/e2e
```

| Variável | Default | Uso |
|---|---|---|
| `MC_IAAS_API_URL` | `http://127.0.0.1:8000` | Base URL |
| `MC_IAAS_API_TOKEN` | vazio | Token fornecido diretamente |
| `MC_IAAS_API_TOKEN_FILE` | `/srv/mc-iaas/secrets/agent-api-token` | Fallback para o token |
| `MC_IAAS_REQUEST_TIMEOUT_SECONDS` | `90` | Timeout HTTP |
| `MC_IAAS_MINECRAFT_TIMEOUT_SECONDS` | `300` | Primeiro boot/readiness |
| `MC_IAAS_RCON_TIMEOUT_SECONDS` | `60` | Readiness RCON |
| `MC_IAAS_POLL_INTERVAL_SECONDS` | `2` | Polling |

Não há testes unitários versionados.

## 14. Limitações e roadmap

Limitações atuais:

- capacidade fixa de quatro slots;
- API deliberadamente em loopback; transporte permanente até o Control Plane não definido;
- um Bearer token compartilhado, sem rotação, revogação ou múltiplas credenciais;
- Control Plane e scheduler multi-node ainda não implementados;
- dependência de configuração libvirt e scripts privilegiados do host;
- sem restore para volume preservado;
- shutdown síncrono pode aguardar 60 s;
- health Minecraft não garante readiness RCON;
- catálogo com uma única versão Minecraft;
- sem systemd, rotação de logs ou testes unitários versionados.

Status resumido:

- Passo 5 — Compute Agent ✅
- Passo 6 — Quotas, Security & Concurrency ✅
- Passo 7 — Monitoring & Recovery ✅
    - 7.1 Node health/readiness ✅
    - 7.2 Agent status/uptime ✅
    - 7.3 Host metrics ✅
    - 7.4 Instance health/metrics ✅
    - 7.5 Invariant severity ✅
    - 7.6 Recovery/reconciliation ✅
    - 7.7 Operational logging ✅
    - 7.8 Node snapshot ✅
    - 7.9 Controlled failure/recovery validation ✅
- Próximo: Passo 8 — integração com o Control Plane
