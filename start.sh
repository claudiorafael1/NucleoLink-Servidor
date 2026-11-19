#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
umask 077
mkdir -p data logs
chmod 700 data logs
PORT=18781
HEALTH="http://127.0.0.1:${PORT}/api/health"
health() {
 python3 - "$HEALTH" <<'PY' >/dev/null 2>&1
import json,sys,urllib.request
try:
  r=urllib.request.urlopen(sys.argv[1],timeout=1.5)
  o=json.load(r)
  assert r.status == 200 and o.get('ok') is True and o.get('security')=='v3'
except Exception: sys.exit(1)
PY
}
port_open() {
 python3 - <<'PY' >/dev/null 2>&1
import socket
s=socket.socket();s.settimeout(1)
try:s.connect(('127.0.0.1',18781))
except OSError:raise SystemExit(1)
finally:s.close()
PY
}
launch_tunnel() {
 local binary=""
 if [[ -x bin/cloudflared ]];then binary="$PWD/bin/cloudflared";
 elif command -v cloudflared >/dev/null 2>&1;then binary="$(command -v cloudflared)";fi
 if [[ -z "$binary" ]];then
   echo '[ERRO] cloudflared nao encontrado. Servidor local continua ativo.' >&2
   echo 'Instale cloudflared pelo site oficial ou coloque-o em ~/NucleoLink/bin/cloudflared.' >&2
   exit 1
 fi
 if [[ -f .tunnel.pid ]];then
   local pid="$(cat .tunnel.pid)"
   if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null;then
     echo '[INFO] Tunel ja possui processo ativo. Confira logs/tunnel.log.'
     return
   fi
 fi
 : > logs/tunnel.log
 nohup "$binary" tunnel --no-autoupdate --url "http://127.0.0.1:${PORT}" > logs/tunnel.log 2>&1 < /dev/null &
 echo $! > .tunnel.pid
 for _ in $(seq 1 40);do
   local url=""
   url="$(grep -Eom1 'https://[a-z0-9-]+\.trycloudflare\.com' logs/tunnel.log || true)"
   if [[ -n "$url" ]];then
     printf '%s\n' "$url" > public_url.txt
     echo "[HTTPS PUBLICO] $url"
     echo '[ATENCAO] Acesso publico ativado. Relay nao possui criptografia ponta a ponta.'
     return
   fi
   if ! kill -0 "$(cat .tunnel.pid)" 2>/dev/null;then break;fi
   sleep 1
 done
 echo '[ERRO] Tunel nao disponibilizou URL. Confira logs/tunnel.log.' >&2
 exit 1
}
if health;then
 if [[ ! -f .server.pid ]];then
   echo '[ERRO] Ha um servidor v3 respondendo, mas nao foi encontrado o PID gerenciado.' >&2
   echo 'Por seguranca nao vou presumir que seja o processo instalado por este projeto.' >&2
   echo 'Identifique o processo com: ss -ltnp "( sport = :18781 )"' >&2
   exit 1
 fi
 SERVERPID="$(cat .server.pid)"
 SERVERARGS="$(ps -p "$SERVERPID" -o args= 2>/dev/null || true)"
 SERVERCWD="$(readlink -f "/proc/$SERVERPID/cwd" 2>/dev/null || true)"
 if [[ "$SERVERARGS" != *'server/app.py'* ]] || { [[ "$SERVERCWD" != "$PWD" ]] && [[ "$SERVERARGS" != *"$PWD/server/app.py"* ]]; };then
   echo '[ERRO] Processo na porta 18781 nao corresponde ao servidor gerenciado.' >&2
   exit 1
 fi
 echo '[OK] Servidor v3 respondendo em localhost.' 
else
 if port_open;then
   echo '[ERRO] Porta 18781 ocupada por outro processo. Nao vou encerra-lo automaticamente.' >&2
   echo 'Identifique com: ss -ltnp "( sport = :18781 )"' >&2
   exit 1
 fi
 python3 -m py_compile server/app.py
 echo '[INFO] Iniciando servidor local...'
 nohup env LINK_HOST=127.0.0.1 LINK_PORT="$PORT" python3 -u server/app.py > logs/server.log 2>&1 < /dev/null &
 echo $! > .server.pid
 for _ in $(seq 1 40);do
   if health;then break;fi
   if ! kill -0 "$(cat .server.pid)" 2>/dev/null;then break;fi
   sleep 0.25
 done
 if ! health;then
    echo '[ERRO] Servidor nao iniciou. Ultimas linhas do log:' >&2
    tail -n 50 logs/server.log >&2 || true
    exit 1
 fi
 echo '[OK] Servidor iniciado.'
fi
echo '[NAVEGADOR] http://127.0.0.1:18781'
echo '[SALAS] bash ~/NucleoLink/criar_sala.sh'
echo '[APROVAR] bash ~/NucleoLink/aprovar.sh CODIGO'
echo '[STATUS] bash ~/NucleoLink/status.sh'
if [[ "${LINK_PUBLIC:-0}" == 1 ]];then launch_tunnel;
else echo '[PRIVACIDADE] Internet desativada por padrao. Para ativar: LINK_PUBLIC=1 bash ~/NucleoLink/start.sh';fi
