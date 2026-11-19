#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import secrets, hashlib, sqlite3, time
from pathlib import Path
path=Path('data/chat.sqlite3')
if not path.exists():raise SystemExit('Execute bash start.sh primeiro.')
c=sqlite3.connect(path)
room=secrets.token_hex(6);secret=secrets.token_hex(24)
c.execute('INSERT INTO rooms(id,secret_hash,created) VALUES(?,?,?)',(room,hashlib.sha256(secret.encode()).hexdigest(),int(time.time())))
c.commit()
public=Path('public_url.txt').read_text().strip() if Path('public_url.txt').exists() else 'http://127.0.0.1:18781'
print('CONVITE (trate como segredo):',public.rstrip('/')+'/#room='+room+'&key='+secret)
print('Ao abrir, o navegador precisara ser autorizado com bash aprovar.sh CODIGO')
PY
