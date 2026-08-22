# Jorge Agent

Agente responsável pelo controle local do Compute Node JORGE no MC-IaaS.

## Responsabilidades

O agente será responsável por interagir com:

- libvirt/QEMU/KVM;
- armazenamento das instâncias;
- rede virtual `mc-net`;
- alocação de slots de execução;
- firewall e publicação de portas;
- ciclo de vida das VMs;
- workloads Minecraft;
- métricas e consoles.

## Execução

O agente será executado diretamente no host Ubuntu e gerenciado pelo systemd.

Ele não será inicialmente containerizado porque necessita acesso privilegiado a recursos do host, especialmente libvirt, storage e networking.

## Desenvolvimento

O código é desenvolvido fora do Compute Node e distribuído pelo GitHub.

Fluxo esperado:

1. desenvolvimento no notebook;
2. commit e push;
3. pull no Compute Node;
4. execução e testes.
