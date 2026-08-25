#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PID_FILE="/srv/mc-iaas/run/jorge-agent.pid"

echo "======================================"
echo "        MC-IaaS Agent Stop"
echo "======================================"
echo

PID=""

if [[ -f "$PID_FILE" ]]; then
    PID="$(cat "$PID_FILE" 2>/dev/null || true)"

    if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
        echo "Parando jorge-agent (PID $PID)..."
        kill -TERM "$PID"
    else
        PID=""
    fi
fi


# Fallback para o caso de o Uvicorn ter sido
# iniciado manualmente e não existir PID file.
if [[ -z "$PID" ]]; then
    PID="$(
        pgrep -u "$(id -u)" \
            -f 'uvicorn jorge_agent.main:app.*--port 8000' \
            | head -n 1 \
            || true
    )"

    if [[ -n "$PID" ]]; then
        echo "jorge-agent encontrado (PID $PID)."
        echo "Encerrando..."
        kill -TERM "$PID"
    fi
fi


if [[ -z "$PID" ]]; then
    echo "jorge-agent já está parado."
    rm -f "$PID_FILE"
    exit 0
fi


for attempt in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        rm -f "$PID_FILE"

        echo
        echo "jorge-agent encerrado ✅"
        exit 0
    fi

    sleep 1
done


echo "O agente não encerrou em 10 segundos."
echo "Enviando SIGKILL..."

kill -KILL "$PID" 2>/dev/null || true
rm -f "$PID_FILE"

echo
echo "jorge-agent encerrado ✅"
