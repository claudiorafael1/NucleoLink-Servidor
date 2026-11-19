#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
stop_file() {
 local f="$1" match="$2"
 [[ -f "$f" ]] || return 0
 local pid;pid="$(cat "$f")"
 if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null;then
   local args="";args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
   local cw="";cw="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
   if [[ "$args" == *"$match"* ]] && { [[ "$cw" == "$PWD" ]] || [[ "$args" == *"$PWD/$match"* ]]; };then
     kill "$pid" 2>/dev/null || true
     echo "[OK] Encerrado PID $pid"
   else
     echo "[AVISO] PID $pid nao corresponde a $match. Nao encerrado." >&2
   fi
 fi
 rm -f "$f"
}
stop_file .tunnel.pid 'cloudflared'
stop_file .server.pid 'server/app.py'
rm -f public_url.txt
echo '[OK] Comando de parada concluido.'
