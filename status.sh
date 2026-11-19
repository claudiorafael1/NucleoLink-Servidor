#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 - <<'PY'
import json,urllib.request
try:
 r=urllib.request.urlopen('http://127.0.0.1:18781/api/health',timeout=2)
 o=json.load(r)
 print('[OK] Servidor respondeu:',o)
except Exception as e:
 print('[ERRO] Sem resposta do servidor:',e)
 raise SystemExit(1)
PY
if [[ -f public_url.txt ]];then echo "[PUBLICO] $(cat public_url.txt)";fi
