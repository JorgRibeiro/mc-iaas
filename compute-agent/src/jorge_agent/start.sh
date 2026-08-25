#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMPUTE_AGENT_DIR="$ROOT_DIR/compute-agent"
VENV_DIR="$COMPUTE_AGENT_DIR/.venv"

LOG_DIR="/srv/mc-iaas/logs"
RUN_DIR="/srv/mc-iaas/run"

LOG_FILE="$LOG_DIR/jorge-agent.log"
PID_FILE="$RUN_DIR/jorge-agent.pid"

AGENT_URL="http://127.0.0.1:8000"


echo "======================================"
echo "        MC-IaaS Compute Node"
echo "======================================"
echo


echo "[1/5] Verificando rede mc-net..."

if virsh net-list --name | grep -qx "mc-net"; then
    echo "mc-net já está ativa."
else
    virsh net-start mc-net
    echo "mc-net iniciada."
fi


echo
echo "[2/5] Verificando storage pools..."

for pool in mc-images mc-instances mc-volumes; do
    if virsh pool-list --name | grep -qx "$pool"; then
        echo "$pool já está ativo."
    else
        virsh pool-start "$pool"
        echo "$pool iniciado."
    fi
done


echo
echo "[3/5] Aplicando firewall MC-IaaS..."

sudo -n /srv/mc-iaas/scripts/apply-firewall.sh

echo "Firewall aplicado."


echo
echo "[4/5] Verificando jorge-agent..."

if curl -fsS "$AGENT_URL/health" >/dev/null 2>&1; then
    echo "jorge-agent já está rodando."
else
    if [[ ! -x "$VENV_DIR/bin/uvicorn" ]]; then
        echo "ERRO: Uvicorn não encontrado em:"
        echo "$VENV_DIR/bin/uvicorn"
        exit 1
    fi

    mkdir -p "$LOG_DIR"
    mkdir -p "$RUN_DIR"

    cd "$COMPUTE_AGENT_DIR"

    nohup "$VENV_DIR/bin/uvicorn" \
        jorge_agent.main:app \
        --host 127.0.0.1 \
        --port 8000 \
        >> "$LOG_FILE" 2>&1 &

    AGENT_PID=$!

    echo "$AGENT_PID" > "$PID_FILE"

    echo "jorge-agent iniciado com PID $AGENT_PID."
fi


echo
echo "[5/5] Aguardando API..."

for attempt in {1..15}; do
    if curl -fsS "$AGENT_URL/health" >/dev/null 2>&1; then
        echo
        echo "======================================"
        echo "       Compute Node PRONTO ✅"
        echo "======================================"
        echo
        echo "API:"
        echo "  $AGENT_URL"
        echo
        echo "Health:"
        curl -fsS "$AGENT_URL/health"
        echo
        echo
        echo "Log:"
        echo "  $LOG_FILE"

        exit 0
    fi

    sleep 1
done


echo
echo "ERRO: jorge-agent não respondeu."
echo
echo "Últimas linhas do log:"
echo

tail -n 30 "$LOG_FILE" 2>/dev/null || true

exit 1
