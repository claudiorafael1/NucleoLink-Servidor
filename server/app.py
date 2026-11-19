#!/usr/bin/env python3
"""Nucleo Link secured relay. stdlib, intentionally no trust in client headers."""
import hashlib, hmac, ipaddress, json, os, re, secrets, sqlite3, threading, time, socket
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
DB = DATA / 'chat.sqlite3'
ADMIN = DATA / 'admin.token'
MAX_BODY = 4096
LOCK = threading.RLock()
BUCKET = defaultdict(deque)
PEERS = {}  # ephemeral room + device directory, not persisted; LAN only
ROOM_RE = re.compile(r'[0-9a-f]{12}\Z')
SECRET_RE = re.compile(r'[0-9a-f]{48}\Z')
TOKEN_RE = re.compile(r'[0-9a-f]{64}\Z')
ID_RE = re.compile(r'[0-9a-f]{32}\Z')


def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

def db():
    c = sqlite3.connect(DB, timeout=5)
    c.execute('PRAGMA busy_timeout=5000')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, secret_hash TEXT NOT NULL, created INTEGER NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL, ts INTEGER NOT NULL)')
    c.execute('CREATE INDEX IF NOT EXISTS room_idx ON messages(room,id)')
    c.execute('CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY, room TEXT NOT NULL, name TEXT NOT NULL, token_hash TEXT NOT NULL, created INTEGER NOT NULL, revoked INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS pairing (id TEXT PRIMARY KEY, room TEXT NOT NULL, name TEXT NOT NULL, code TEXT NOT NULL UNIQUE, proof_hash TEXT NOT NULL, issued INTEGER NOT NULL, approved INTEGER DEFAULT 0, token TEXT)')
    c.execute('CREATE INDEX IF NOT EXISTS pairing_exp ON pairing(issued)')
    return c

def admin_token():
    if not ADMIN.exists():
        try:
            fd = os.open(str(ADMIN), os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            with os.fdopen(fd,'w') as f: f.write(secrets.token_hex(32)+'\n')
        except FileExistsError: pass
    os.chmod(ADMIN, 0o600)
    return ADMIN.read_text().strip()

def room_ok(room, secret):
    if not ROOM_RE.fullmatch(room) or not SECRET_RE.fullmatch(secret): return False
    with db() as c: row = c.execute('SELECT secret_hash FROM rooms WHERE id=?',(room,)).fetchone()
    return bool(row and hmac.compare_digest(row[0],sha(secret)))

def device_ok(room, dev, token):
    if not ID_RE.fullmatch(dev) or not TOKEN_RE.fullmatch(token):return False
    with db() as c: row=c.execute('SELECT token_hash,revoked FROM devices WHERE id=? AND room=?',(dev,room)).fetchone()
    return bool(row and not row[1] and hmac.compare_digest(row[0],sha(token)))

def limited(name, count, interval):
    now=time.monotonic()
    with LOCK:
        q=BUCKET[name]
        while q and q[0]<now-interval:q.popleft()
        if len(q)>=count:return True
        q.append(now)
        # Bound memory consumption under attempted IP spoofing
        if len(BUCKET)>12000:
            for k in list(BUCKET)[:3000]:
                if not BUCKET[k] or BUCKET[k][-1]<now-interval: BUCKET.pop(k,None)
        return False

class LimitedServer(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=32
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.slots=threading.BoundedSemaphore(32)
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try: super().process_request(request,client_address)
        except Exception:
            self.slots.release()
            raise
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()

class Handler(BaseHTTPRequestHandler):
    server_version='NucleoLink/3'
    protocol_version='HTTP/1.0'
    def setup(self):
        super().setup()
        self.connection.settimeout(7)
    def log_message(self,fmt,*args):
        # No secrets, URLs, body or auth headers in logs
        print('http',self.client_address[0],self.command,urlsplit(self.path).path,flush=True)
    def respond(self,code,obj):
        raw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        self.headers_common(code,'application/json; charset=utf-8',len(raw))
        try:self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError):pass
    def headers_common(self,code,kind,size):
        self.send_response(code)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(size))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
    def json_body(self):
        length=self.headers.get('Content-Length','')
        if not length.isdigit() or not 0<int(length)<=MAX_BODY:raise ValueError('size')
        if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':raise ValueError('type')
        value=json.loads(self.rfile.read(int(length)))
        if not isinstance(value,dict):raise ValueError('json object')
        return value
    def ip(self):
        # Cloudflare tunnel is loopback; do not trust spoofable forwarded IP for authorization.
        return self.client_address[0]
    def room(self):
        room=self.headers.get('X-Room','')
        raw=self.headers.get('Authorization','')
        secret=raw[7:] if raw.startswith('Bearer ') else ''
        return room if room_ok(room,secret) else None
    def authorized(self,room):
        dev=self.headers.get('X-Device-ID','')
        tok=self.headers.get('X-Device-Token','')
        # All clients including browsers require an approved device token.
        return device_ok(room,dev,tok)
    def do_GET(self):
        path=urlsplit(self.path)
        if limited(('all',self.ip()),360,60):return self.respond(429,{'error':'Limite temporario'})
        if path.path=='/api/health':return self.respond(200,{'ok':True,'product':'Nucleo Link','security':'v3','p2p':'lan-udp-aes256gcm'})
        if path.path=='/api/pair/status':
            if limited(('pairpoll',self.ip()),120,60):return self.respond(429,{'error':'Limite de consultas'})
            args=parse_qs(path.query)
            pid=args.get('id',[''])[0]; proof=self.headers.get('X-Pair-Proof','')
            if not ID_RE.fullmatch(pid) or not TOKEN_RE.fullmatch(proof):return self.respond(400,{'error':'Pedido invalido'})
            with LOCK,db() as c:
                c.execute('DELETE FROM pairing WHERE issued<?',(int(time.time())-600,))
                row=c.execute('SELECT approved,token,proof_hash FROM pairing WHERE id=?',(pid,)).fetchone()
                if not row or not hmac.compare_digest(row[2],sha(proof)):return self.respond(404,{'error':'Pareamento expirado'})
                if not row[0]:return self.respond(200,{'status':'pending'})
                token=row[1]
                c.execute('DELETE FROM pairing WHERE id=?',(pid,))
                return self.respond(200,{'status':'approved','token':token,'device_id':pid})
        if path.path=='/api/p2p/peers':
            room=self.room()
            if not room or not self.authorized(room):return self.respond(401,{'error':'Acesso negado'})
            if limited(('peers',room),240,60):return self.respond(429,{'error':'Limite de consultas'})
            myid=self.headers.get('X-Device-ID','')
            now=time.monotonic()
            with LOCK:
                for k,v in list(PEERS.items()):
                    if v['expires']<now:PEERS.pop(k,None)
                peers=[{'id':k[1],'ip':v['ip'],'port':v['port']} for k,v in PEERS.items() if k[0]==room and k[1]!=myid][:8]
            return self.respond(200,{'peers':peers,'mode':'LAN somente; relay permanece disponivel'})
        if path.path=='/api/messages':
            room=self.room()
            if not room or not self.authorized(room):return self.respond(401,{'error':'Acesso negado'})
            if limited(('read',room),240,60):return self.respond(429,{'error':'Limite temporario'})
            try:after=max(0,min(2147483647,int(parse_qs(path.query).get('after',['0'])[0])))
            except (TypeError,ValueError):after=0
            with db() as c: rows=c.execute('SELECT id,sender,body,ts FROM messages WHERE room=? AND id>? ORDER BY id LIMIT 60',(room,after)).fetchall()
            return self.respond(200,{'messages':[dict(zip(('id','sender','body','ts'),x)) for x in rows]})
        if path.path in ('/','/index.html','/app.js','/style.css'):
            file=ROOT/'web'/('index.html' if path.path=='/' else path.path[1:])
            try:data=file.read_bytes()
            except OSError:return self.respond(404,{'error':'Arquivo ausente'})
            kind='text/html; charset=utf-8' if file.suffix=='.html' else ('text/javascript; charset=utf-8' if file.suffix=='.js' else 'text/css; charset=utf-8')
            self.headers_common(200,kind,len(data));return self.wfile.write(data)
        self.respond(404,{'error':'Nao encontrado'})
    def do_POST(self):
        path=urlsplit(self.path).path
        if limited(('post',self.ip()),120,60):return self.respond(429,{'error':'Limite temporario'})
        try: obj=self.json_body()
        except (ValueError,TypeError,UnicodeError,json.JSONDecodeError):return self.respond(400,{'error':'JSON invalido'})
        if path=='/api/rooms':
            supplied=self.headers.get('X-Admin-Token','')
            if limited(('room_create',self.ip()),10,300):return self.respond(429,{'error':'Tente mais tarde'})
            if not supplied or not hmac.compare_digest(supplied,admin_token()):return self.respond(403,{'error':'Token de administrador necessario'})
            room=secrets.token_hex(6);secret=secrets.token_hex(24)
            with db() as c:c.execute('INSERT INTO rooms VALUES(?,?,?)',(room,sha(secret),int(time.time())))
            return self.respond(201,{'room':room,'secret':secret})
        if path=='/api/pair/start':
            room=self.room()
            if not room:return self.respond(401,{'error':'Convite invalido'})
            if limited(('pair_start',room),6,600) or limited(('pair_global',),60,600):return self.respond(429,{'error':'Muitos pedidos de pareamento'})
            name=obj.get('name','Cardputer')
            proof=obj.get('proof','')
            if not isinstance(name,str) or not isinstance(proof,str) or not TOKEN_RE.fullmatch(proof):return self.respond(400,{'error':'Dados invalidos'})
            name=name.strip()[:24] or 'Cardputer'; pid=secrets.token_hex(16)
            now=int(time.time())
            with LOCK,db() as c:
                c.execute('DELETE FROM pairing WHERE issued<?',(now-600,))
                for _ in range(8):
                    code=f'{secrets.randbelow(10**10):010d}'
                    try:
                        c.execute('INSERT INTO pairing(id,room,name,code,proof_hash,issued) VALUES(?,?,?,?,?,?)',(pid,room,name,code,sha(proof),now))
                        break
                    except sqlite3.IntegrityError:continue
                else:return self.respond(503,{'error':'Tente novamente'})
            return self.respond(201,{'id':pid,'code':code,'expires':600})
        if path=='/api/p2p/announce':
            room=self.room()
            if not room or not self.authorized(room):return self.respond(401,{'error':'Acesso negado'})
            if limited(('announce',room),80,60):return self.respond(429,{'error':'Limite de anuncios'})
            rawip=obj.get('ip');port=obj.get('port')
            if not isinstance(rawip,str) or not isinstance(port,int) or isinstance(port,bool) or port!=18782:
                return self.respond(400,{'error':'Endereco invalido'})
            try:
                ip=ipaddress.ip_address(rawip)
                if ip.version!=4 or not ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
                    raise ValueError()
            except ValueError:return self.respond(400,{'error':'Somente IPv4 privada LAN'})
            dev=self.headers.get('X-Device-ID','')
            with LOCK:
                PEERS[(room,dev)]={'ip':str(ip),'port':port,'expires':time.monotonic()+100}
                if len(PEERS)>5000:
                    now=time.monotonic()
                    for k,v in list(PEERS.items()):
                        if v['expires']<now:PEERS.pop(k,None)
            return self.respond(200,{'ok':True,'ttl':100})
        if path=='/api/messages':
            room=self.room()
            if not room or not self.authorized(room):return self.respond(401,{'error':'Acesso negado'})
            if limited(('send',room),45,60):return self.respond(429,{'error':'Limite de mensagens'})
            sender=obj.get('sender','');body=obj.get('body','')
            if not isinstance(sender,str) or not isinstance(body,str):return self.respond(400,{'error':'Tipos invalidos'})
            sender=sender.strip();body=body.strip()
            if not 1<=len(sender)<=28 or not 1<=len(body)<=400:return self.respond(400,{'error':'Tamanho invalido'})
            if any(ord(c)<32 and c not in '\n\t' for c in body+sender):return self.respond(400,{'error':'Caracter invalido'})
            with LOCK,db() as c:
                c.execute('INSERT INTO messages(room,sender,body,ts) VALUES(?,?,?,?)',(room,sender,body,int(time.time())))
                c.execute('DELETE FROM messages WHERE room=? AND id<(SELECT COALESCE(MAX(id),0)-500 FROM messages WHERE room=?)',(room,room))
            return self.respond(201,{'ok':True})
        self.respond(404,{'error':'Nao encontrado'})

if __name__=='__main__':
    os.umask(0o077)
    db().close();admin_token()
    host=os.environ.get('LINK_HOST','127.0.0.1')
    if host not in ('127.0.0.1','::1'):raise SystemExit('Host publico bloqueado: use tunel HTTPS')
    port=int(os.environ.get('LINK_PORT','18781'))
    print(f'Nucleo Link secured on {host}:{port}',flush=True)
    LimitedServer((host,port),Handler).serve_forever()
