#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 - "${1:-}" <<'PY'
import sqlite3,sys
from pathlib import Path
if not Path('data/chat.sqlite3').exists():sys.exit('Banco nao encontrado')
c=sqlite3.connect('data/chat.sqlite3')
rows=c.execute('SELECT id,name,room,revoked FROM devices ORDER BY created DESC').fetchall()
print('DISPOSITIVOS:')
for id,name,room,revoked in rows:print(id,name,'sala='+room,'REVOGADO' if revoked else 'ATIVO')
id=sys.argv[1]
if id:
 if id not in [x[0] for x in rows]:sys.exit('ID nao encontrado')
 if input('Digitar REVOGAR para bloquear: ')=='REVOGAR':
  c.execute('UPDATE devices SET revoked=1 WHERE id=?',(id,));c.commit();print('Revogado.')
 else:print('Cancelado.')
else:print('Para revogar: bash revogar.sh ID_DO_DISPOSITIVO')
PY
