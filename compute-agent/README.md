**# MC-IaaS Compute Agent**

O \`jorge-agent\` é o daemon/API local do Compute Node JORGE. Ele recebe operações de alto nível sobre instâncias Minecraft e as transforma em mudanças reais no hypervisor, storage, rede e filesystem do host.

Este documento descreve o componente implementado. Para a visão geral do projeto e a arquitetura Control Plane/Compute Node, consulte o [README principal]\(../README.md).

**## Visão geral**

O agente é uma aplicação FastAPI executada no mesmo host que KVM/QEMU e libvirt. Os scripts atuais mantêm a API vinculada a \`http\://127.0.0.1:8000\`, de forma que ela não fica diretamente exposta à LAN ou à Internet. O acesso administrativo HTTP e WebSocket também possui autenticação própria por Bearer token.

O único endpoint HTTP deliberadamente público é \`GET /health\`, usado como liveness probe pelo próprio host. Os demais endpoints administrativos exigem \`Authorization: Bearer <token>\`. A documentação automática do FastAPI (\`/docs\`, \`/redoc\` e \`/openapi.json\`) está desabilitada para não criar superfícies públicas adicionais.

O token do agente é um secret operacional do Compute Node, armazenado fora do Git em \`/srv/mc-iaas/secrets/agent-api-token\`, com permissão restrita. O futuro Control Plane deverá possuir esse secret — ou outro mecanismo de distribuição/rotação que o substitua — para autenticar chamadas ao Compute Node. O transporte remoto entre Control Plane e Compute Node ainda não foi definido; manter o bind em loopback evita expor a API antes dessa decisão.

Um START percorre aproximadamente este caminho:

\`\`\`text

POST /instances/{name}/start
        ↓
autenticação Bearer
        ↓
instance\_service
        ↓
lock exclusivo da instância
        ↓
lock global de runtime
        ↓
runtime\_service
        ├── seleciona slot
        ├── cria MAC e NIC
        ├── reserva DHCP
        ├── atualiza port-forward
        └── aplica firewall
        ↓
domain\_service
        └── inicia o domínio libvirt

\`\`\`

O agente mantém a separação entre recursos persistentes, criados no CREATE, e recursos de runtime, consumidos somente no START. O Passo 6 também consolidou regras de concorrência, quotas, lifecycle e segurança para impedir alocações duplicadas e operações administrativas não autenticadas.

**## Responsabilidades**

\- criar e remover domínios libvirt;

\- criar overlays de sistema e volumes persistentes;

\- produzir seeds NoCloud com cloud-init;

\- gerar credenciais de VM e secrets de RCON;

\- orquestrar CREATE, START, STOP, RESTART e DELETE;

\- serializar operações mutáveis por instância;

\- proteger alocação/liberação de runtime com lock global;

\- impor quotas de CPU, memória e capacidade de runtime;

\- alocar e liberar slots de runtime;

\- gerenciar NIC, MAC, reservas e leases DHCP;

\- manter configuração de port-forward e aplicar firewall;

\- inicializar Minecraft dentro da VM;

\- executar comandos RCON;

\- autenticar endpoints administrativos HTTP e WebSocket;

\- expor somente o liveness básico sem autenticação;

\- expor health e métricas;

\- oferecer consoles WebSocket;

\- reconciliar runtime órfão no startup;

\- verificar invariantes do Compute Node.

**## Arquitetura interna**

\`\`\`mermaid

flowchart TB

    CLIENT["Cliente local / futuro Control Plane"]

    MAIN["main.py\<br/>FastAPI + lifespan"]

    INSTANCE["instance\_service\<br/>orquestração do lifecycle"]

    DOMAIN["domain\_service\<br/>domínios libvirt"]

    STORAGE["storage\_service\<br/>overlays e volumes"]

    CLOUD["cloud\_init\_service\<br/>seed e bootstrap"]

    RUNTIME["runtime\_service\<br/>slot + NIC + DHCP + firewall"]

    META["metadata\_service"]

    SECRET["secret\_service"]

    LIBVIRT\_SERVICE["libvirt\_service\<br/>consulta e estados"]

    HEALTH["health\_service"]

    METRICS["metrics\_service"]

    RCON["rcon\_service"]

    CONSOLES["console services e bridges"]

    RECOVERY["recovery\_service"]

    INVARIANTS["invariant\_service"]

    HV["libvirt / KVM / QEMU"]

    HOST["filesystem + scripts do host"]

    CLIENT --> MAIN

    MAIN --> INSTANCE

    MAIN --> LIBVIRT\_SERVICE

    MAIN --> HEALTH

    MAIN --> METRICS

    MAIN --> RCON

    MAIN --> CONSOLES

    MAIN --> RECOVERY

    MAIN --> INVARIANTS

    INSTANCE --> DOMAIN

    INSTANCE --> STORAGE

    INSTANCE --> CLOUD

    INSTANCE --> RUNTIME

    INSTANCE --> META

    INSTANCE --> SECRET

    DOMAIN --> HV

    STORAGE --> HV

    RUNTIME --> HV

    RUNTIME --> HOST

    CLOUD --> HOST

    META --> HOST

    SECRET --> HOST

\`\`\`

\`main.py\` contém a borda HTTP/WebSocket e o lifecycle de startup. \`instance\_service.py\` é a camada de orquestração das mutações; os demais services encapsulam responsabilidades específicas.

**## API atual**

| Método | Endpoint | Autenticação | Responsabilidade |
|---|---|---|---|
| \`GET\` | \`/health\` | pública | health básico do processo |
| \`GET\` | \`/hypervisor/health\` | Bearer | versão, host e contagem de domínios libvirt |
| \`GET\` | \`/instances\` | Bearer | lista instâncias definidas |
| \`POST\` | \`/instances\` | Bearer | cria storage, cloud-init, domínio, metadata e secrets |
| \`GET\` | \`/instances/{name}\` | Bearer | detalhe de uma instância |
| \`POST\` | \`/instances/{name}/start\` | Bearer | aloca runtime e inicia a VM |
| \`POST\` | \`/instances/{name}/stop\` | Bearer | para a VM e libera runtime |
| \`POST\` | \`/instances/{name}/restart\` | Bearer | reinicia mantendo runtime |
| \`DELETE\` | \`/instances/{name}\` | Bearer | remove a instância parada; aceita \`delete_data\` |
| \`GET\` | \`/instances/{name}/health\` | Bearer | estado da VM e do Minecraft |
| \`GET\` | \`/instances/{name}/metrics\` | Bearer | CPU, memória, storage e rede |
| \`POST\` | \`/instances/{name}/minecraft/command\` | Bearer | executa comando RCON |
| \`WS\` | \`/instances/{name}/console\` | Bearer no handshake | console serial da VM |
| \`WS\` | \`/instances/{name}/minecraft/console\` | Bearer no handshake | console de comandos Minecraft via RCON |

**### Modelo de segurança da API**

A segurança implementada no Passo 6 usa autenticação máquina-a-máquina simples. Não existe login de usuário, sessão, OAuth ou JWT no Compute Agent. O objetivo do agente é receber comandos de um Control Plane confiável, portanto um Bearer token compartilhado é suficiente para a arquitetura atual e mantém o componente pequeno.

O header esperado é:

\`\`\`http

Authorization: Bearer <agent-api-token>

\`\`\`

A validação está centralizada em \`services/auth_service.py\`. HTTP e WebSocket reutilizam a mesma leitura e comparação do token. A comparação usa \`secrets.compare_digest()\`, evitando comparar credenciais sensíveis com igualdade comum.

Comportamento HTTP:

\`\`\`text

GET /health
    sem token               → 200

endpoint administrativo
    sem token               → 401
    token inválido          → 401
    token válido            → executa endpoint
    secret do agente ausente/vazio
                            → 503

\`\`\`

O endpoint \`/health\` é deliberadamente público porque os scripts locais precisam descobrir se o processo está vivo sem depender do secret. Ele não fornece inventário, configuração do hypervisor ou dados das VMs.

Os WebSockets são autenticados durante o handshake, antes de entrar nos bridges de console. Uma conexão sem credencial válida é rejeitada antes de \`websocket.accept()\`; nos testes manuais com Postman o handshake sem token foi rejeitado com HTTP \`403 Forbidden\`, enquanto o mesmo endpoint conectou com o Bearer token correto. Como a dependência de autenticação é executada antes da função do endpoint, uma conexão não autenticada não chega a abrir o console libvirt nem o console Minecraft/RCON.

**### Armazenamento do token**

O secret do agente fica em:

\`\`\`text

/srv/mc-iaas/secrets/agent-api-token

\`\`\`

Ele não deve ser versionado, inserido na metadata de instâncias, impresso em logs ou copiado para documentação. No host JORGE ele é mantido com acesso restrito ao usuário operacional.

O caminho do secret é centralizado em \`PATHS.agent_api_token_file\`. \`auth_service.py\` lê o valor no momento da validação, recusa arquivo ausente ou vazio e nunca devolve o token na resposta.

**### Superfície de exposição**

O Uvicorn continua iniciado com:

\`\`\`text

--host 127.0.0.1
--port 8000

\`\`\`

Autenticação e bind em loopback resolvem problemas diferentes:

\- o **bind em loopback** impede conexões diretas pela rede;

\- o **Bearer token** impede que um cliente que consiga alcançar a API execute operações sem credencial.

Durante desenvolvimento, o notebook pode acessar o agente por túnel SSH, por exemplo encaminhando \`localhost:8000\` para \`127.0.0.1:8000\` do JORGE. Isso permite testar a API sem abrir a porta 8000 publicamente.

A integração remota permanente com o futuro Control Plane ainda deve decidir o canal de transporte. A existência do Bearer token não deve ser usada como justificativa para publicar a porta 8000 indiscriminadamente na Internet.

**### Consumidores internos autenticados**

O \`stop-final.sh\` consulta \`/instances\` e chama \`/instances/{name}/stop\`. Após a introdução da autenticação, ele passou a carregar o token de \`/srv/mc-iaas/secrets/agent-api-token\` e enviar o Bearer header nas chamadas administrativas. O probe \`/health\` continua sem credencial.

A suíte E2E também foi preparada para construir um único \`httpx.Client\` autenticado. O token pode ser fornecido por variável de ambiente ou pelo arquivo local do Compute Node, evitando repetir headers em cada requisição e evitando credenciais hardcoded no repositório.

**### Documentação automática**

\`/docs\`, \`/redoc\` e \`/openapi.json\` estão desabilitados na aplicação atual. Isso mantém a regra operacional simples: \`/health\` é a única rota HTTP pública; as rotas administrativas conhecidas são registradas em um \`APIRouter\` protegido por \`Depends(require_api_token)\`.

**### Lifecycle e conflitos**

As operações mutáveis também seguem uma política explícita de estado:

| Situação | Resultado |
|---|---|
| CREATE de nome inexistente | cria instância parada |
| CREATE de nome existente | \`409 Conflict\` |
| START de instância parada | inicia e aloca runtime |
| START de instância já ativa | \`409 Conflict\` |
| STOP de instância ativa | para e libera runtime |
| STOP de instância já parada | sucesso idempotente |
| RESTART de instância ativa | reinicia preservando runtime |
| RESTART de instância parada | \`409 Conflict\` |
| DELETE de instância ativa | \`409 Conflict\` |
| DELETE de instância parada | remove conforme \`delete_data\` |
| operação sobre instância inexistente | \`404 Not Found\` |

DELETE não funciona como um STOP implícito. A transição destrutiva exige explicitamente \`RUNNING → STOP → STOPPED → DELETE\`, o que reduz ambiguidade operacional e evita que uma requisição de remoção encerre uma VM ativa silenciosamente.

**## Fluxos principais**

\`\`\`mermaid

stateDiagram-v2

    [\*] --> Stopped: CREATE cria recursos persistentes

    Stopped --> Running: START aloca runtime e inicia VM

    Running --> Running: RESTART preserva runtime

    Running --> Stopped: STOP encerra VM e libera runtime

    Stopped --> [\*]: DELETE remove recursos

\`\`\`

**### CREATE**

\`\`\`mermaid

sequenceDiagram

    participant API as FastAPI

    participant I as instance\_service

    participant S as storage\_service

    participant SEC as secret\_service

    participant C as cloud\_init\_service

    participant D as domain\_service

    participant M as metadata\_service

    API->>I: create\_instance(payload)

    I->>S: cria overlay e volume persistente

    I->>SEC: gera secret RCON

    I->>C: cria user-data, meta-data e seed

    I->>D: define domínio libvirt parado

    I->>M: salva metadata

    I-->>API: STOPPED, runtime = null

\`\`\`

O payload precisa aceitar a EULA. O schema permite memória entre 512 e 2048 MiB, fixa \`vcpus\` em 1 e usa Minecraft \`26.2\` como versão padrão e atualmente catalogada.

Se a senha da VM não for informada, \`credential\_service.py\` gera uma senha e o CREATE a devolve uma vez em \`generated\_password\`. O hash usado pelo cloud-init é produzido com \`sha512\_crypt\`. O valor não é gravado na metadata.

O rollback do CREATE ocorre na ordem inversa para domínio, cloud-init, storage e secrets quando uma etapa falha. CREATE não anexa NIC, não reserva IP e não publica porta.

**### START**

O runtime é preparado antes do boot:

1\. confirma que o domínio existe e está parado;

2\. consulta reservas DHCP, leases IPv4 e portas publicadas;

3\. escolhe o primeiro slot disponível;

4\. deriva uma MAC determinística do nome da instância;

5\. anexa uma interface VirtIO persistente ao domínio;

6\. adiciona uma reserva DHCP live e persistente;

7\. grava o port-forward do Minecraft;

8\. executa o script de firewall;

9\. inicia o domínio libvirt.

Se a preparação falhar, \`runtime\_service.py\` executa ações de rollback em ordem inversa. Se o boot do domínio falhar depois da preparação, \`instance\_service.py\` chama a liberação de runtime.

**### STOP**

\`domain\_service.py\` solicita shutdown gracioso e aguarda até 60 segundos. Depois que a VM está inativa, o runtime é liberado:

1\. leases DHCP IPv4 são liberados pelo helper do host;

2\. a regra de port-forward é removida e o firewall reaplicado;

3\. a reserva DHCP é removida;

4\. a NIC persistente é destacada.

Falhas de cleanup são agregadas em \`RuntimeCleanupError\`, permitindo relatar mais de um recurso que não pôde ser removido.

**### RESTART**

RESTART exige uma VM ativa com runtime existente. O agente envia \`reboot(0)\` ao domínio e retorna a mesma alocação de slot, IP e porta. DHCP, NIC e port-forward não são recriados.

**### DELETE**

DELETE exige que a VM já esteja parada. Uma tentativa de remover uma instância ativa retorna conflito em vez de executar STOP implicitamente. Depois dessa pré-condição, o agente libera qualquer runtime residual e remove domínio, cloud-init, secrets e disco de sistema.

\| Parâmetro | Resultado |

\|---|---|

\| \`delete\_data=false\` | preserva o volume RAW do mundo e marca a metadata como deletada |

\| \`delete\_data=true\` | remove também volume de dados e metadata |

O default é \`delete\_data=false\`. Ainda não existe um endpoint de restore para uma metadata marcada como deletada.

**## Contrato da máquina virtual**

O domínio criado atualmente possui:

\- tipo \`kvm\` e arquitetura \`x86\_64\`;

\- 1 vCPU;

\- memória configurável entre 512 MiB e 2 GiB;

\- firmware/boot convencional por disco;

\- ACPI e APIC;

\- console serial PTY;

\- nenhuma NIC no CREATE;

\- Ubuntu 24.04 Minimal como imagem base;

\- OpenJDK 25 e Minecraft instalados pelo cloud-init.

Mapeamento dos discos:

\| Dispositivo | Formato | Função |

\|---|---|---|

\| \`vda\` | QCOW2 | sistema operacional, baseado na imagem base |

\| \`vdb\` | RAW, somente leitura | seed NoCloud do cloud-init |

\| \`vdc\` | RAW | dados persistentes montados em \`/srv/minecraft\` |

A interface de rede VirtIO é anexada somente no START e removida no STOP.

**## Storage**

Os nomes de pools configurados são:

\| Pool | Uso atual |

\|---|---|

\| \`mc-images\` | pool de imagens ativado pelos scripts de infraestrutura |

\| \`mc-instances\` | overlays QCOW2 dos discos de sistema |

\| \`mc-volumes\` | volumes RAW persistentes do Minecraft |

O agente lê a imagem base diretamente em:

\`\`\`text

/srv/mc-iaas/storage/images/ubuntu-24.04-minimal-base.qcow2

\`\`\`

O disco de sistema tem 10 GiB e usa a imagem base como backing store. O volume de dados tem 5 GiB e allocation inicial igual a zero. A invariante exige que a imagem base exista e não tenha bits de escrita.

Os diretórios de backing dos pools \`mc-instances\` e \`mc-volumes\` são definidos na configuração libvirt do host; o código Python trabalha com os nomes dos pools, não fixa esses backing paths.

**## Runtime slots**

\`RuntimeSlot\` possui três campos:

\`\`\`text

slot
ip
external_port

\`\`\`

| Slot | IP | Porta externa |
|---:|---|---:|
| 1 | \`10.50.0.10\` | \`25565\` |
| 2 | \`10.50.0.11\` | \`25566\` |
| 3 | \`10.50.0.12\` | \`25567\` |
| 4 | \`10.50.0.13\` | \`25568\` |

Um slot é consumido no START e liberado no STOP. A seleção ignora slots com IP reservado, lease IPv4 ativo ou porta externa já presente no arquivo de port-forward. A capacidade de runtime é derivada dos quatro \`RUNTIME_SLOTS\`; portanto, no estado atual, o quinto START simultaneamente ativo não possui slot e retorna conflito.

**### Concorrência e locks**

O Passo 6 introduziu serialização explícita das operações mutáveis através de \`services/lock_service.py\`. Os locks usam \`fcntl.flock()\` sobre arquivos em \`/srv/mc-iaas/run/locks\`, portanto funcionam entre processos e não apenas entre threads Python.

Existem dois níveis:

\- **lock por instância:** impede duas operações mutáveis concorrentes sobre a mesma VM;

\- **lock global de runtime:** protege recursos compartilhados entre VMs — slots, reservas DHCP, port-forwards e alterações de firewall.

A ordem oficial de aquisição é:

\`\`\`text

instance lock
    ↓
runtime lock

\`\`\`

O código não deve adquirir esses locks na ordem inversa. Essa regra reduz risco de deadlock quando uma operação precisa dos dois recursos.

CREATE, START, STOP, RESTART e DELETE são serializados por instância. START e STOP entram no lock global somente durante a fase de alocação/liberação do runtime; o lock global não permanece preso durante um boot ou shutdown potencialmente lento.

No START, por exemplo:

\`\`\`text

lock(instance)
    ↓
verifica estado
    ↓
lock(runtime)
    ↓
aloca slot + NIC + DHCP + port-forward
    ↓
libera lock(runtime)
    ↓
inicia domínio
    ↓
se boot falhar:
    lock(runtime)
    ↓
rollback do runtime
    ↓
libera lock(instance)

\`\`\`

Isso preserva atomicidade da alocação sem bloquear todas as outras VMs durante o boot.

Foram realizados testes manuais de concorrência com múltiplos START/STOP:

\- START simultâneo de VMs diferentes recebeu slots distintos;

\- STOP simultâneo liberou corretamente os runtimes;

\- dois STARTs simultâneos da mesma VM resultaram em uma execução bem-sucedida e um conflito, sem duplicar lease ou port-forward;

\- START e STOP concorrentes da mesma VM foram serializados e terminaram em estado coerente.

Os testes automáticos específicos de concorrência foram deliberadamente adiados; a proteção implementada e os testes manuais não devem ser confundidos com uma suíte formal de stress/concurrency.

**## Networking**

**### Rede e endereçamento**

O agente usa a rede libvirt \`mc-net\`, no espaço \`10.50.0.0/24\`. O helper de liberação DHCP opera sobre a bridge \`virbr50\`.

A MAC de cada instância é determinística:

\`\`\`text

52:54:00 + primeiros 3 bytes de SHA-256(nome)

\`\`\`

Isso permite reencontrar reservas e interfaces pelo nome ou pela MAC.

**### DHCP**

No START, o agente adiciona um elemento DHCP host à configuração live e persistente da rede. No STOP, chama \`/srv/mc-iaas/scripts/release-dhcp-lease.sh\` para cada lease IPv4 e remove a reserva.

O helper versionado em \`infra/scripts/release-dhcp-lease.sh\` valida IP e MAC antes de executar \`/usr/bin/dhcp\_release\` na \`virbr50\`. Ele precisa ser instalado no caminho esperado pelo agente.

**### Port-forward e firewall**

As regras desejadas ficam em:

\`\`\`text

/srv/mc-iaas/config/port-forwards.conf

\`\`\`

Cada linha contém porta externa, IP interno e porta interna. Depois de adicionar ou remover uma entrada, o agente executa:

\`\`\`text

/srv/mc-iaas/scripts/apply-firewall.sh

\`\`\`

Esse script é uma dependência operacional do host, mas não está versionado neste checkout. O START também o executa antes de subir a API.

Minecraft usa \`25565\` dentro da VM. RCON usa \`25575\` e não é publicado pelo port-forward. \`invariant\_service.py\` sinaliza qualquer regra cujo destino interno seja a porta RCON.

**## Metadata e secrets**

**### Metadata**

Arquivos em \`/srv/mc-iaas/metadata/{name}.json\` guardam:

\- nome da instância;

\- usuário da VM;

\- versão do Minecraft;

\- memória e vCPUs;

\- caminho do volume de dados;

\- marcadores de deleção e preservação quando aplicável.

O formato JSON é usado por listagem, detalhes, recovery e invariantes. Metadata marcada como \`deleted\` é ignorada por recovery e invariantes de domínio.

**### Secrets**

Arquivos em \`/srv/mc-iaas/secrets/{name}.json\` guardam somente o secret RCON da instância. O diretório recebe modo \`0700\`; o arquivo é criado atomicamente com \`O\_EXCL\` e modo \`0600\`.

O secret é gerado com \`secrets.token\_urlsafe(24)\`. Valores reais de senha nunca devem ser copiados para documentação, logs ou testes.

**## Cloud-init**

Artefatos por instância são criados em:

\`\`\`text

/srv/mc-iaas/cloud-init/{name}/

├── user-data

├── meta-data

└── seed.img

\`\`\`

\`cloud-localds\` transforma \`user-data\` e \`meta-data\` em um seed NoCloud. O seed é anexado como \`vdb\` via VirtIO e somente leitura.

Em alto nível, o cloud-init:

\- cria o usuário solicitado e configura sua senha hash;

\- instala OpenJDK 25 e \`curl\`;

\- cria usuário e grupo \`minecraft\` com UID/GID 2000;

\- formata \`vdc\` como ext4 quando necessário;

\- registra o volume em \`/etc/fstab\` e o monta em \`/srv/minecraft\`;

\- baixa e valida o servidor por SHA-1;

\- grava a EULA aceita;

\- configura RCON;

\- instala e inicia \`minecraft.service\`.

O catálogo de artefatos suporta atualmente a versão Minecraft \`26.2\` com URL e hash fixados no serviço.

**## Minecraft e RCON**

\| Serviço | Porta interna | Exposição |

\|---|---:|---|

\| Minecraft | \`25565\` | publicado pelo slot de runtime |

\| RCON | \`25575\` | somente comunicação interna do agente |

\`rcon\_service.py\` implementa autenticação e pacotes do protocolo RCON diretamente sobre TCP. O agente carrega o secret local e se conecta ao IP privado da VM. Os valores \`SERVERDATA\_\*\` pertencem ao protocolo, não à configuração operacional.

Existe uma janela normal de readiness em que a porta Minecraft já aceita conexões, mas RCON ainda responde \`Connection refused\`. Por isso, a suíte E2E possui retry separado para o primeiro comando RCON.

**### Console da VM versus console Minecraft**

\- **\*\*VM serial console:\*\*** \`console\_service.py\` abre um stream libvirt para o console serial do domínio; \`console\_bridge.py\` transporta bytes entre esse stream e um WebSocket.

\- **\*\*Minecraft console:\*\*** \`minecraft\_console\_bridge.py\` recebe comandos de texto por WebSocket e os executa via RCON. Não é um terminal do sistema operacional.

**## Health e métricas**

**### Health**

\`health\_service.py\` combina estado do domínio, runtime e uma conexão TCP à porta Minecraft:

\| Estado Minecraft | Significado |

\|---|---|

\| \`stopped\` | domínio não está ativo |

\| \`online\` | domínio ativo, runtime presente e porta \`25565\` acessível |

\| \`unavailable\` | domínio ativo sem runtime ou porta não acessível |

O probe TCP usa timeout de 1 segundo. Ele verifica disponibilidade da porta Minecraft, não readiness do RCON.

**### Métricas**

O endpoint de métricas coleta:

\- CPU: tempo acumulado e uso percentual amostrado por 0,5 segundo;

\- memória: configurada, corrente e RSS quando disponível;

\- storage: capacidade e allocation de sistema e dados;

\- rede: bytes recebidos e transmitidos pelas interfaces do domínio.

Valores como CPU, RSS, allocation e contadores de rede são dinâmicos.

**## Recovery**

\`recovery\_service.py\` percorre metadata não deletada e domínios existentes durante o startup. Para cada instância:

\- VM ativa: estado mantido;

\- VM parada sem runtime: estado mantido;

\- VM parada com runtime: \`release\_instance\_runtime()\` é executado;

\- metadata sem nome ou sem domínio: recovery não toma decisão destrutiva;

\- falhas individuais: registradas em \`RecoveryReport.errors\`.

\`main.py\` interrompe o startup se o relatório contiver erros. Depois do recovery, executa as invariantes e também interrompe o startup se o Compute Node não estiver saudável.

**## Invariantes**

\`invariant\_service.py\` verifica atualmente:

\- existência e atividade da rede \`mc-net\`;

\- existência e atividade dos pools \`mc-instances\` e \`mc-volumes\`;

\- existência da imagem base;

\- ausência de permissão de escrita na imagem base;

\- existência dos scripts de firewall e liberação DHCP;

\- ausência de encaminhamento público para RCON;

\- validade mínima da metadata não deletada;

\- existência de domínio para cada metadata gerenciada;

\- VM ativa deve possuir runtime;

\- VM parada não deve possuir runtime;

\- disponibilidade da conexão libvirt.

O serviço não verifica atualmente, por exemplo, permissões de secrets, conteúdo integral do cloud-init ou atividade do pool \`mc-images\`. Esses itens não devem ser assumidos como invariantes implementadas.

**## Configuração centralizada**

\`src/jorge_agent/config.py\` concentra configuração estática compartilhada:

| Objeto | Conteúdo |
|---|---|
| \`LIBVIRT\` | URI \`qemu:///system\`, rede \`mc-net\` e nomes dos pools |
| \`STORAGE\` | raiz, imagem base e tamanhos dos discos |
| \`NETWORK\` | portas, arquivo de forwards e scripts do host |
| \`PATHS\` | diretórios de cloud-init, metadata, secrets, runtime, locks e caminho do token da API |
| \`QUOTAS\` | limites e defaults de memória/vCPU |
| \`RUNTIME_SLOTS\` | quatro combinações slot/IP/porta |
| \`MAX_ACTIVE_INSTANCES\` | capacidade derivada de \`len(RUNTIME_SLOTS)\` |

A política atual de recursos é:

\`\`\`text

memória:
    mínimo  = 512 MiB
    default = 2048 MiB
    máximo  = 2048 MiB

vCPU:
    mínimo  = 1
    default = 1
    máximo  = 1

instâncias ativas:
    máximo estrutural = 4 slots

\`\`\`

Pydantic rejeita CREATE fora dos limites de memória/vCPU com erro de validação. O quinto START não é bloqueado por um contador paralelo; ele falha naturalmente porque nenhum \`RuntimeSlot\` está disponível. Essa escolha evita duas fontes de verdade para capacidade.

Os services importam esses objetos em vez de repetir caminhos e números. Estado dinâmico, leases, senhas, tokens reais e métricas não pertencem a \`config.py\`; apenas seus caminhos e limites estáticos são configurados ali.

**## Estrutura dos arquivos**

\`\`\`text

compute-agent/

├── pyproject.toml

├── start.sh

├── stop.sh

├── stop-final.sh

├── tests/

│   └── e2e/

│       ├── \_\_init\_\_.py

│       └── test\_instance\_lifecycle.py

└── src/

    └── jorge\_agent/

        ├── \_\_init\_\_.py

        ├── config.py

        ├── main.py

        ├── schemas/

        │   ├── \_\_init\_\_.py

        │   └── instance.py

        └── services/

            ├── \_\_init\_\_.py

            ├── auth\_service.py

            ├── cloud\_init\_service.py

            ├── console\_bridge.py

            ├── console\_service.py

            ├── credential\_service.py

            ├── domain\_service.py

            ├── health\_service.py

            ├── instance\_service.py

            ├── invariant\_service.py

            ├── libvirt\_service.py

            ├── lock\_service.py

            ├── metadata\_service.py

            ├── metrics\_service.py

            ├── minecraft\_console\_bridge.py

            ├── rcon\_service.py

            ├── recovery\_service.py

            ├── runtime\_service.py

            ├── secret\_service.py

            └── storage\_service.py

\`\`\`

Responsabilidade de cada módulo:

\| Arquivo | Responsabilidade real |

\|---|---|

\| \`config.py\` | dataclasses e objetos de configuração estática compartilhada |

\| \`main.py\` | aplicação FastAPI, endpoints, WebSockets e startup recovery/invariants |

\| \`schemas/instance.py\` | validação de entrada, enums e modelos públicos de resposta |

\| \`services/instance\_service.py\` | orquestra lifecycle, locks e rollback entre services |
| \`services/auth\_service.py\` | valida Bearer token para HTTP e WebSocket e lê o secret do agente |
| \`services/lock\_service.py\` | implementa locks exclusivos por instância e lock global de runtime com \`flock\` |

\| \`services/domain\_service.py\` | define XML do domínio e controla start, shutdown, reboot e undefine |

\| \`services/storage\_service.py\` | cria e remove overlays e volumes nos pools libvirt |

\| \`services/cloud\_init\_service.py\` | gera configuração NoCloud e bootstrap da VM/Minecraft |

\| \`services/runtime\_service.py\` | aloca slot e gerencia NIC, DHCP, lease, forwards e firewall |

\| \`services/metadata\_service.py\` | persiste e lê descrição não secreta da instância |

\| \`services/secret\_service.py\` | gera, protege, lê e remove secret RCON |

\| \`services/credential\_service.py\` | resolve senha fornecida ou gera credencial da VM |

\| \`services/libvirt\_service.py\` | mapeia estados e fornece listagem/detalhe/hypervisor health |

\| \`services/health\_service.py\` | combina estado da VM com probe TCP do Minecraft |

\| \`services/metrics\_service.py\` | coleta CPU, memória, volumes e interfaceStats |

\| \`services/rcon\_service.py\` | implementa protocolo e execução de comando RCON |

\| \`services/console\_service.py\` | mantém conexão e stream do console serial libvirt |

\| \`services/console\_bridge.py\` | bridge assíncrona entre stream serial e WebSocket |

\| \`services/minecraft\_console\_bridge.py\` | bridge WebSocket de comandos para RCON |

\| \`services/recovery\_service.py\` | reconcilia runtime de VMs paradas no startup |

\| \`services/invariant\_service.py\` | verifica pré-condições e coerência operacional do nó |

\| \`\_\_init\_\_.py\` | marca os diretórios como pacotes; não contém lógica atualmente |

**## Dependências entre services**

\`\`\`mermaid

graph TD

    MAIN[main] --> AUTH[auth\_service]

    MAIN --> INSTANCE[instance\_service]

    MAIN --> LIBVIRT\_S[libvirt\_service]

    MAIN --> HEALTH[health\_service]

    MAIN --> METRICS[metrics\_service]

    MAIN --> RCON[rcon\_service]

    MAIN --> CB[console\_bridge]

    MAIN --> MCB[minecraft\_console\_bridge]

    MAIN --> RECOVERY[recovery\_service]

    MAIN --> INVARIANT[invariant\_service]

    INSTANCE --> LOCK[lock\_service]

    INSTANCE --> DOMAIN[domain\_service]

    INSTANCE --> STORAGE[storage\_service]

    INSTANCE --> CLOUD[cloud\_init\_service]

    INSTANCE --> CREDENTIAL[credential\_service]

    INSTANCE --> RUNTIME[runtime\_service]

    INSTANCE --> META[metadata\_service]

    INSTANCE --> SECRET[secret\_service]

    LIBVIRT\_S --> META

    LIBVIRT\_S --> RUNTIME

    HEALTH --> LIBVIRT\_S

    HEALTH --> RUNTIME

    METRICS --> LIBVIRT\_S

    RCON --> RUNTIME

    RCON --> SECRET

    MCB --> RCON

    CB --> CONSOLE[console\_service]

    RECOVERY --> RUNTIME

    INVARIANT --> RUNTIME

\`\`\`

O principal ponto de acoplamento é \`instance\_service.py\`, que conhece os services necessários para cada transição e aplica os locks de lifecycle. \`runtime\_service.py\` reúne responsabilidades que atravessam libvirt, XML de rede, filesystem e subprocessos privilegiados. \`auth\_service.py\` permanece na borda da aplicação: autentica chamadas antes que elas alcancem os services de infraestrutura.

**## Diretórios operacionais**

O layout esperado no Compute Node é aproximadamente:

\`\`\`text

/srv/mc-iaas/

├── storage/

│   ├── images/

│   │   └── ubuntu-24.04-minimal-base.qcow2

│   ├── instances/          # backing esperado do pool mc-instances

│   └── volumes/            # backing esperado do pool mc-volumes

├── cloud-init/

│   └── {instance}/

├── metadata/

├── secrets/
│   ├── agent-api-token        # Bearer token do Compute Agent
│   └── {instance}.json        # secret RCON por instância

├── config/

│   └── port-forwards.conf

├── scripts/

│   ├── apply-firewall.sh

│   └── release-dhcp-lease.sh

├── logs/

│   └── jorge-agent.log

└── run/
    ├── jorge-agent.pid
    └── locks/
        ├── runtime.lock
        └── instances/
            └── {name}.lock

\`\`\`

Os caminhos de \`instances/\` e \`volumes/\` dependem da configuração efetiva dos pools libvirt. O script \`apply-firewall.sh\` e a instalação dos helpers no host não estão integralmente representados neste checkout.

**## Scripts de lifecycle**

**### \`compute-agent/start.sh\`**

1\. verifica e inicia \`mc-net\`;

2\. verifica e inicia os três pools;

3\. aplica o firewall;

4\. inicia Uvicorn com \`nohup\` se a API não estiver ativa;

5\. grava PID, aguarda \`/health\` e mostra o caminho do log.

O repositório também contém \`../start.sh\`, que cumpre papel semelhante a partir da raiz, mas usa verificações \`virsh\` mais diretas. Os dois scripts não são wrappers um do outro.

**### \`compute-agent/stop.sh\`**

Para somente o processo \`jorge-agent\`. Usa o PID file e, como fallback, procura o processo Uvicorn. Depois de 10 segundos, envia \`SIGKILL\`. Não para VMs, rede ou pools.

**### \`compute-agent/stop-final.sh\`**

Executa shutdown operacional completo:

1\. garante que o agente esteja disponível;

2\. lista e para graciosamente todas as instâncias;

3\. verifica invariantes;

4\. para o agente;

5\. desativa \`mc-net\` e os pools em ordem inversa.

Os dados persistentes são preservados. Esse script não equivale a DELETE das instâncias. Como \`/instances\` e os endpoints de STOP são administrativos, o script carrega o Bearer token local e autentica essas chamadas; \`/health\` permanece sem autenticação.

Não há unit de systemd do agente versionada atualmente; o gerenciamento implementado neste checkout usa scripts, \`nohup\`, log e PID file.

**## Como executar**

**### Pré-requisitos**

O host precisa fornecer:

\- Linux com KVM/QEMU e libvirt;

\- Python 3.11 ou superior;

\- \`cloud-localds\`;

\- rede \`mc-net\` e pools libvirt configurados;

\- imagem base no caminho esperado;

\- helpers de DHCP e firewall instalados;

\- permissões/sudo não interativo para os scripts necessários.

**### Ambiente Python**

Na raiz de \`compute-agent/\`:

\`\`\`bash

python3 -m venv .venv

.venv/bin/python -m pip install -e '.[compute,dev]'

\`\`\`

O extra \`compute\` instala \`libvirt-python\`; o extra \`dev\` instala \`pytest\` e \`httpx\`.

**### Inicialização**

\`\`\`bash

./start.sh

\`\`\`

Para desenvolvimento local no Compute Node, a aplicação também pode ser iniciada diretamente:

\`\`\`bash

.venv/bin/python -m uvicorn \\

    jorge\_agent.main\:app \\

    \--host 127.0.0.1 \\

    \--port 8000

\`\`\`

Health básico:

\`\`\`bash

curl -fsS http\://127.0.0.1:8000/health

\`\`\`


**### Secret de autenticação do agente**

Antes de iniciar uma versão protegida do agente no Compute Node, o arquivo abaixo precisa existir e conter um token não vazio:

\`\`\`text

/srv/mc-iaas/secrets/agent-api-token

\`\`\`

Uma instalação típica deve restringir o arquivo ao usuário operacional, por exemplo modo \`0600\`. O token deve ser gerado com fonte criptograficamente segura e nunca commitado no Git.

Exemplo de chamada administrativa local:

\`\`\`bash

TOKEN="$(< /srv/mc-iaas/secrets/agent-api-token)"

curl -fsS \
    -H "Authorization: Bearer $TOKEN" \
    http://127.0.0.1:8000/instances

unset TOKEN

\`\`\`

Para desenvolvimento a partir de outro computador, prefira um túnel SSH em vez de alterar o bind do Uvicorn apenas para testes:

\`\`\`text

notebook:127.0.0.1:8000
        ↓
      SSH
        ↓
JORGE:127.0.0.1:8000

\`\`\`


**## Testes**

A suíte em \`tests/e2e/test\_instance\_lifecycle.py\` usa \`pytest\` e \`httpx\` contra a API real. O cliente HTTP é configurado com Bearer token uma vez e todas as requisições administrativas herdam o header. Ela cobre:

\`\`\`text

API health e invariantes

→ CREATE / GET / LIST

→ START e readiness

→ health / metrics / RCON

→ RESTART e novo readiness

→ STOP

→ segundo START / STOP

→ DELETE destrutivo

→ verificação de artefatos

→ invariantes finais

\`\`\`

O teste cria VM, volumes e regras de rede reais. Por segurança, é marcado com \`e2e\` e ignorado sem opt-in explícito.

No Compute Node JORGE:

\`\`\`bash

MC\_IAAS\_RUN\_E2E=1 \\

.venv/bin/python -m pytest \\

    -v -s -m e2e tests/e2e

\`\`\`

Usar \`python -m pytest\` garante que o pytest executado pertence ao mesmo Python do venv que contém \`libvirt-python\` e o pacote editável.

Variáveis opcionais:

\| Variável | Default | Uso |

\|---|---:|---|

\| \`MC\_IAAS\_API\_URL\` | \`http\://127.0.0.1:8000\` | base URL da API |
| \`MC\_IAAS\_API\_TOKEN\` | vazio | token Bearer fornecido diretamente ao E2E |
| \`MC\_IAAS\_API\_TOKEN\_FILE\` | \`/srv/mc-iaas/secrets/agent-api-token\` | arquivo usado quando o token não é fornecido por variável |

\| \`MC\_IAAS\_REQUEST\_TIMEOUT\_SECONDS\` | \`90\` | timeout HTTP |

\| \`MC\_IAAS\_MINECRAFT\_TIMEOUT\_SECONDS\` | \`300\` | primeiro boot/readiness |

\| \`MC\_IAAS\_RCON\_TIMEOUT\_SECONDS\` | \`60\` | readiness RCON |

\| \`MC\_IAAS\_POLL\_INTERVAL\_SECONDS\` | \`2\` | intervalo de polling |

Sem opt-in, a coleta é segura:

\`\`\`bash

.venv/bin/python -m pytest -m e2e

\# resultado esperado: skipped

\`\`\`

Não há atualmente testes unitários versionados.

**## Limitações atuais**

\- somente quatro slots de runtime;

\- API deliberadamente restrita ao loopback; transporte remoto permanente para o Control Plane ainda não definido;

\- autenticação atual usa um Bearer token compartilhado; rotação, revogação e múltiplas credenciais não estão implementadas;

\- Control Plane e scheduler distribuído não implementados;

\- configuração libvirt e scripts privilegiados dependem do host;

\- ausência de restore para volume preservado;

\- shutdown síncrono pode aguardar até 60 segundos;

\- health Minecraft não implica readiness imediata do RCON;

\- catálogo com uma única versão Minecraft;

\- ausência de testes unitários e de uma suíte automática específica de concorrência/segurança;

\- integração WAN e múltiplos Compute Nodes não validados neste código;

\- os limites adicionais para mensagens de console/WebSocket além das validações já existentes ainda podem ser endurecidos no futuro.

**## Próximos passos**

Evoluções coerentes com o estado atual incluem:

\- definir um canal remoto privado/seguro entre Control Plane e Compute Agent sem expor indiscriminadamente a porta 8000;

\- definir distribuição, rotação e revogação do token de agente para múltiplos Compute Nodes;

\- scheduler e inventário de múltiplos nós;

\- observabilidade agregada do host e dos workloads;

\- restore explícito de mundos preservados;

\- gerenciamento do agente por systemd em vez de apenas \`nohup\`/PID file;

\- testes unitários, testes automáticos de concorrência e cenários de falha controlada;

\- endurecer limites de mensagens de console/RCON caso o Control Plane passe a aceitar entrada menos confiável.

Autenticação Bearer, locks de concorrência e quotas básicas já fazem parte do estado implementado e não devem mais ser descritos como trabalho futuro.


**## Checkpoint do Passo 6 — quotas, segurança e concorrência**

O Passo 6 consolidou três propriedades que antes estavam incompletas na infraestrutura:

1. **Concorrência:** mutações da mesma instância são serializadas e a alocação compartilhada de runtime possui lock global. O modelo evita que duas chamadas concorrentes consumam o mesmo slot/IP/porta.

2. **Quotas:** CREATE é validado para memória de 512–2048 MiB e 1 vCPU; a capacidade simultânea do nó é limitada pelos quatro slots de runtime.

3. **Segurança:** somente \`/health\` permanece público; HTTP administrativo e WebSockets exigem Bearer token, o secret fica fora do Git, Swagger/OpenAPI público foi desabilitado e consumidores internos foram adaptados para autenticar.

Também foi formalizada a política de conflitos do lifecycle, especialmente a exigência de STOP antes de DELETE.

Os cenários principais foram validados manualmente no Compute Node JORGE. Os testes automáticos específicos de concorrência, quotas e segurança foram adiados e permanecem como dívida de testes, não como ausência das proteções de runtime descritas acima.


**## Evolução da arquitetura interna**

O agente está organizado principalmente por services. A leitura das dependências evidencia alguns limites de domínio que podem orientar uma modularização futura sem determinar uma estrutura definitiva:

\- **\*\*virtualization:\*\*** domínio, estado libvirt e console serial;

\- **\*\*storage:\*\*** imagem base, overlays e volumes persistentes;

\- **\*\*runtime/network:\*\*** slots, NIC, DHCP, leases, port-forward e firewall;

\- **\*\*provisioning:\*\*** cloud-init, credenciais e bootstrap;

\- **\*\*minecraft:\*\*** RCON, health e console de comandos;

\- **\*\*observability:\*\*** health, métricas e invariantes;

\- **\*\*persistence:\*\*** metadata e secrets;

\- **\*\*orchestration/recovery:\*\*** lifecycle, rollback e reconciliação.

Hoje, \`instance\_service.py\` coordena vários desses limites e \`runtime\_service.py\` concentra operações de rede e infraestrutura. Tornar essas fronteiras explícitas na documentação facilita avaliar, no futuro, onde separar contratos sem alterar prematuramente uma implementação que já funciona.