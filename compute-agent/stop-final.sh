#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMPUTE_AGENT_DIR="$ROOT_DIR"
PYTHON="$COMPUTE_AGENT_DIR/.venv/bin/python"

AGENT_URL="http://127.0.0.1:8000"


echo "======================================"
echo "      MC-IaaS Final Shutdown"
echo "======================================"
echo


echo "[1/5] Verificando jorge-agent..."

if ! curl -fsS "$AGENT_URL/health" >/dev/null 2>&1; then
    echo "jorge-agent está parado."
    echo "Iniciando temporariamente para"
    echo "encerrar as VMs corretamente..."

    "$ROOT_DIR/start.sh"

    sleep 1
else
    echo "jorge-agent está ativo."
fi


echo
echo "[2/5] Encerrando instâncias..."

INSTANCES="$(
    curl -fsS "$AGENT_URL/instances"
)"

mapfile -t INSTANCE_DATA < <(
    printf '%s' "$INSTANCES" |
        "$PYTHON" -c '
import json
import sys

instances = json.load(sys.stdin)

for instance in instances:
    print(
        instance["name"]
        + "\t"
        + instance["state"]
    )
'
)


if [[ ${#INSTANCE_DATA[@]} -eq 0 ]]; then
    echo "Nenhuma instância encontrada."
fi


for entry in "${INSTANCE_DATA[@]}"; do
    IFS=$'\t' read -r NAME STATE <<< "$entry"

    echo
    echo "Instância: $NAME"
    echo "Estado:    $STATE"

    case "$STATE" in

        stopped)
            echo "Já está parada."
            ;;

        paused)
            echo "Retomando VM pausada..."

            virsh resume "$NAME"

            echo "Encerrando graciosamente..."

            curl -fsS -X POST \
                "$AGENT_URL/instances/$NAME/stop"

            echo
            ;;

        *)
            echo "Encerrando graciosamente..."

            curl -fsS -X POST \
                "$AGENT_URL/instances/$NAME/stop"

            echo
            ;;

    esac
done


echo
echo "[3/5] Verificando consistência..."

cd "$COMPUTE_AGENT_DIR"

"$PYTHON" -c '
from jorge_agent.services.invariant_service import (
    check_invariants,
)

report = check_invariants()

if not report.healthy:
    print()
    print("ERRO: Compute Node inconsistente.")

    for issue in report.issues:
        target = (
            f" [{issue.instance}]"
            if issue.instance
            else ""
        )

        print(
            f"- {issue.code}{target}: "
            f"{issue.detail}"
        )

    raise SystemExit(1)

print("Estado consistente.")
'


echo
echo "[4/5] Encerrando jorge-agent..."

"$ROOT_DIR/stop.sh"


echo
echo "[5/5] Desativando infraestrutura..."


if virsh net-list --name | grep -qx "mc-net"; then
    echo "Desativando mc-net..."
    virsh net-destroy mc-net
else
    echo "mc-net já está inativa."
fi


for pool in \
    mc-volumes \
    mc-instances \
    mc-images
do
    if "$PYTHON" -c '
import libvirt
import sys

pool_name = sys.argv[1]

conn = libvirt.open("qemu:///system")

try:
    pool = conn.storagePoolLookupByName(pool_name)
    sys.exit(0 if pool.isActive() else 1)
finally:
    conn.close()
' "$pool"; then

        echo "Desativando $pool..."
        virsh -c qemu:///system pool-destroy "$pool"

    else
        echo "$pool já está inativo."
    fi
done


echo
echo "======================================"
echo "       MC-IaaS DESLIGADO ✅"
echo "======================================"
echo
echo "VMs:          paradas"
echo "jorge-agent:  parado"
echo "mc-net:       parada"
echo "storage:      desativado"
echo
echo "Dados persistentes foram preservados."
