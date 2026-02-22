#!/bin/zsh

set -euo pipefail

robot_url="${1:-}"
port="${2:-8001}"
host="0.0.0.0"

base_cmd=(python3 workbench/server.py --port "$port" --host "$host")

if [[ -n "$robot_url" ]]; then
  export ROBOT_BASE_URL="$robot_url"
fi

echo "Starting workbench on http://$host:$port/"
if [[ -n "$robot_url" ]]; then
  echo "Open: http://127.0.0.1:$port/?robot=$robot_url"
else
  echo "Open: http://127.0.0.1:$port/"
  echo "Tip: pass robot url: ./start-workbench.sh http://192.168.2.182"
fi

exec "${base_cmd[@]}"
