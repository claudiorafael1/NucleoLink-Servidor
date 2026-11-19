import json, tempfile, pathlib, urllib.request, urllib.error, os, subprocess, sys, time, shutil, secrets
with tempfile.TemporaryDirectory() as tmp:
 root=pathlib.Path(tmp)
 for folder in ('server','web'):shutil.copytree(pathlib.Path(__file__).resolve().parents[1]/folder,root/folder)
 port='18871';env={**os.environ,'LINK_PORT':port}
 p=subprocess.Popen([sys.executable,str(root/'server'/'app.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 try:
  base='http://127.0.0.1:'+port
  for _ in range(60):
   try:urllib.request.urlopen(base+'/api/health',timeout=.3);break
   except Exception:time.sleep(.1)
  def call(path,data=None,room='',secret='',headers=None):
   h={'X-Room':room,'Authorization':'Bearer '+secret}
   if data is not None:h['Content-Type']='application/json'
   h.update(headers or {})
   req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=h)
   try:
    r=urllib.request.urlopen(req,timeout=3)
    return r.status,json.load(r)
   except urllib.error.HTTPError as e:
    return e.code,json.load(e)
  assert call('/api/rooms',{})[0]==403
  admin=(root/'data'/'admin.token').read_text().strip()
  status,created=call('/api/rooms',{},headers={'X-Admin-Token':admin})
  assert status==201
  room,secret=created['room'],created['secret']
  assert call('/api/messages?after=0',room=room,secret=secret)[0]==401
  proof=secrets.token_hex(32)
  status,request=call('/api/pair/start',{'name':'Cardputer-ADV','proof':proof},room,secret)
  assert status==201
  pid,code=request['id'],request['code']
  assert len(code)==10
  assert call('/api/pair/status?id='+pid,headers={'X-Pair-Proof':'0'*64})[0]==404
  assert call('/api/pair/status?id='+pid,headers={'X-Pair-Proof':proof})[1]['status']=='pending'
  import sqlite3,hashlib
  c=sqlite3.connect(root/'data'/'chat.sqlite3')
  tok=secrets.token_hex(32)
  c.execute('INSERT INTO devices(id,room,name,token_hash,created) VALUES(?,?,?,?,?)',(pid,room,'ADV',hashlib.sha256(tok.encode()).hexdigest(),int(time.time())))
  c.execute('UPDATE pairing SET approved=1,token=? WHERE id=?',(tok,pid));c.commit();c.close()
  approved=call('/api/pair/status?id='+pid,headers={'X-Pair-Proof':proof})
  assert approved[1]['status']=='approved' and approved[1]['token']==tok
  assert call('/api/pair/status?id='+pid,headers={'X-Pair-Proof':proof})[0]==404
  dev={'X-Device-ID':pid,'X-Device-Token':tok}
  assert call('/api/p2p/peers',room=room,secret=secret)[0]==401
  assert call('/api/p2p/announce',{'ip':'8.8.8.8','port':18782},room,secret,dev)[0]==400
  assert call('/api/p2p/announce',{'ip':'192.168.1.20','port':18782},room,secret,dev)[0]==200
  assert call('/api/p2p/peers',room=room,secret=secret,headers=dev)[1]['peers']==[]
  assert call('/api/messages',{'sender':'V1','body':'Hello ADV'},room,secret,dev)[0]==201
  assert call('/api/messages?after=0',room=room,secret=secret,headers=dev)[1]['messages'][0]['body']=='Hello ADV'
  assert call('/api/messages',{'sender':'a','body':'x'*401},room,secret,dev)[0]==400
  c=sqlite3.connect(root/'data'/'chat.sqlite3');c.execute('UPDATE devices SET revoked=1 WHERE id=?',(pid,));c.commit();c.close()
  assert call('/api/messages?after=0',room=room,secret=secret,headers=dev)[0]==401
  print('PASS: admin, pairing, token, send, receive, length, revocation')
 finally:
  p.terminate();p.wait(timeout=5)
