#!/usr/bin/env bash
# Nucleo Link: instalador EXCLUSIVAMENTE do servidor, idempotente, sem sudo.
set -Eeuo pipefail
umask 077
SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TARGET="${NUCLEOLINK_HOME:-$HOME/NucleoLink}"
[[ "$TARGET" == /* ]] || { echo '[ERRO] NUCLEOLINK_HOME deve ser caminho absoluto.' >&2;exit 1; }
if ! command -v python3 >/dev/null 2>&1;then
 echo '[ERRO] Instale o Python 3 pelo gerenciador de pacotes do Linux Mint.' >&2;exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info<(3,9):raise SystemExit('[ERRO] Python 3.9+ necessario.')
print('[OK] Python:',sys.version.split()[0])
PY
[[ -f "$SOURCE/server/app.py" && -f "$SOURCE/web/index.html" ]] || { echo '[ERRO] Execute o instalador dentro da pasta original do pacote.' >&2;exit 1; }
if [[ "$SOURCE" != "$TARGET" ]];then
 echo "[1/5] Preparando instalacao em $TARGET ..."
 mkdir -p "$TARGET" "$TARGET/backups" "$TARGET/data" "$TARGET/logs"
 chmod 700 "$TARGET/data" "$TARGET/logs" "$TARGET/backups"
 STAMP="$(date +%Y%m%d_%H%M%S)"
 BACKUP="$TARGET/backups/servidor_antes_${STAMP}"
 mkdir -p "$BACKUP"
 for f in server/app.py web/index.html web/app.js web/style.css tests/test_server.py start.sh stop.sh status.sh criar_sala.sh aprovar.sh revogar.sh;do
   if [[ -e "$TARGET/$f" ]];then mkdir -p "$BACKUP/$(dirname "$f")";cp -p "$TARGET/$f" "$BACKUP/$f";fi
 done
 # Desligar apenas processo identificado como o servidor deste diretorio.
 if [[ -f "$TARGET/.server.pid" ]];then
   OLDPID="$(cat "$TARGET/.server.pid")"
   if [[ "$OLDPID" =~ ^[0-9]+$ ]] && kill -0 "$OLDPID" 2>/dev/null;then
      OLDARGS="$(ps -p "$OLDPID" -o args= 2>/dev/null || true)"
      OLDCWD="$(readlink -f "/proc/$OLDPID/cwd" 2>/dev/null || true)"
      if [[ "$OLDARGS" == *'server/app.py'* ]] && { [[ "$OLDCWD" == "$TARGET" ]] || [[ "$OLDARGS" == *"$TARGET/server/app.py"* ]]; };then
        echo "[INFO] Encerrando servidor anterior (PID $OLDPID)..."
        kill "$OLDPID" || true
        for _ in $(seq 1 30);do kill -0 "$OLDPID" 2>/dev/null || break; sleep 0.2;done
      else
        echo '[AVISO] PID registrado pertence a outro processo. Nao sera encerrado.' >&2
      fi
   fi
   rm -f "$TARGET/.server.pid"
 fi
 # O modo publico nunca pode permanecer ativado acidentalmente apos upgrade.
 if [[ -f "$TARGET/.tunnel.pid" ]];then
   TUNPID="$(cat "$TARGET/.tunnel.pid")"
   if [[ "$TUNPID" =~ ^[0-9]+$ ]] && kill -0 "$TUNPID" 2>/dev/null;then
     TUNARGS="$(ps -p "$TUNPID" -o args= 2>/dev/null || true)"
     TUNCWD="$(readlink -f "/proc/$TUNPID/cwd" 2>/dev/null || true)"
     if [[ "$TUNARGS" == *cloudflared* && "$TUNARGS" == *tunnel* && "$TUNCWD" == "$TARGET" ]];then
       echo '[INFO] Desligando tunel publico anterior (seguranca por padrao)...'
       kill "$TUNPID" || true
     else
       echo '[AVISO] O processo do tunel anterior nao foi identificado. Verifique manualmente.' >&2
     fi
   fi
   rm -f "$TARGET/.tunnel.pid"
 fi
 rm -f "$TARGET/public_url.txt"
 mkdir -p "$TARGET/server" "$TARGET/web" "$TARGET/tests" "$TARGET/firmware/builds"
 for f in server/app.py web/index.html web/app.js web/style.css tests/test_server.py start.sh stop.sh status.sh criar_sala.sh aprovar.sh revogar.sh;do
   cp "$SOURCE/$f" "$TARGET/$f"
 done
 chmod 700 "$TARGET"/{start,stop,status,criar_sala,aprovar,revogar}.sh
 for model in cardputer_v1 cardputer_adv;do
   if [[ -s "$SOURCE/firmware/builds/$model.bin" && ! -e "$TARGET/firmware/builds/$model.bin" ]];then cp "$SOURCE/firmware/builds/$model.bin" "$TARGET/firmware/builds/$model.bin";fi
 done
 echo "[OK] Backup de arquivos anteriores: $BACKUP"
else
 echo '[1/5] Instalando na propria pasta do projeto.'
 mkdir -p "$TARGET/data" "$TARGET/logs" "$TARGET/backups" "$TARGET/firmware/builds"
fi
chmod 700 "$TARGET/data" "$TARGET/logs" "$TARGET/backups"
python3 -m py_compile "$TARGET/server/app.py"
echo '[2/5] Testando autenticacao, pareamento e troca de mensagens...'
python3 "$TARGET/tests/test_server.py"
echo '[3/5] Iniciando servidor...'
if ! bash "$TARGET/start.sh";then
 echo '[ERRO] Instalacao interrompida. Confira: ~/NucleoLink/logs/server.log' >&2
 exit 1
fi
echo '[4/5] Confirmando servidor...'
bash "$TARGET/status.sh"
echo '[5/5] Instalacao concluida. Nenhum firmware foi compilado.'
echo "[BIN V1] $TARGET/firmware/builds/cardputer_v1.bin"
echo "[BIN ADV] $TARGET/firmware/builds/cardputer_adv.bin"
echo '[SEGURANCA] Nenhuma porta do roteador foi aberta; acesso externo continua desligado.'
echo "[DOCUMENTACAO] Consulte $SOURCE/README.md"
