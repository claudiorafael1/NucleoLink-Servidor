#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $# -ne 1 || ! "$1" =~ ^[0-9]{10}$ ]];then
 echo 'Uso: bash aprovar.sh CODIGO_DE_10_DIGITOS'
 exit 2
fi
python3 - "$1" <<'PY'
import sys, sqlite3, secrets, hashlib, time
from pathlib import Path
code=sys.argv[1]
db=Path('data/chat.sqlite3')
if not db.exists():sys.exit('Banco nao encontrado; inicie o servidor.')
c=sqlite3.connect(db)
try:
 c.execute('BEGIN IMMEDIATE')
 r=c.execute('SELECT id,room,name,issued,approved FROM pairing WHERE code=?',(code,)).fetchone()
 if not r:sys.exit('Codigo inexistente.')
 pid,room,name,issued,approved=r
 if time.time()-issued>600:sys.exit('Codigo expirado; solicite novo pareamento.')
 if approved:sys.exit('Codigo ja aprovado.')
 print(f'Dispositivo: {name}; sala: {room}; emitido ha {int(time.time()-issued)} segundos')
 answer=input('Confirma que o codigo aparece fisicamente no dispositivo que voce deseja autorizar? [sim/N] ').strip().lower()
 if answer!='sim':sys.exit('Cancelado.')
 token=secrets.token_hex(32)
 c.execute('INSERT INTO devices(id,room,name,token_hash,created) VALUES(?,?,?,?,?)',(pid,room,name,hashlib.sha256(token.encode()).hexdigest(),int(time.time())))
 c.execute('UPDATE pairing SET approved=1,token=? WHERE id=?',(token,pid))
 c.commit()
 print('APROVADO. O dispositivo recebera as credenciais automaticamente.')
except Exception:
 c.rollback()
 raise
finally:c.close()
PY
