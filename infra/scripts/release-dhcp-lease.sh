#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 <ip> <mac>" >&2
    exit 2
fi

IP="$1"
MAC="$2"

if [[ ! "$IP" =~ ^10\.50\.0\.([0-9]{1,3})$ ]]; then
    echo "invalid MC-IaaS IP" >&2
    exit 2
fi

LAST_OCTET="${BASH_REMATCH[1]}"

if (( LAST_OCTET < 1 || LAST_OCTET > 254 )); then
    echo "invalid MC-IaaS IP" >&2
    exit 2
fi

if [[ ! "$MAC" =~ ^52:54:00:([0-9a-fA-F]{2}:){2}[0-9a-fA-F]{2}$ ]]; then
    echo "invalid MC-IaaS MAC" >&2
    exit 2
fi

exec /usr/bin/dhcp_release \
    virbr50 \
    "$IP" \
    "$MAC" \
    '*'
