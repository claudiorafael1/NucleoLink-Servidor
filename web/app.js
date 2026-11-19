'use strict';
const $=s=>document.querySelector(s);
let room='',secret='',cursor=0,timer=null, pairTimer=null, devId='',devToken='';
const toast=t=>{const el=$('#toast');el.textContent=t;el.style.display='block';setTimeout(()=>el.style.display='none',6500)};
async function api(path,method='GET',data,extra={}){
 const h={'X-Room':room,'Authorization':'Bearer '+secret,...extra};
 if(devId&&devToken){h['X-Device-ID']=devId;h['X-Device-Token']=devToken;}
 if(data)h['Content-Type']='application/json';
 const r=await fetch(path,{method,headers:h,body:data?JSON.stringify(data):undefined,cache:'no-store'});
 const o=await r.json();if(!r.ok)throw Error(o.error||'Erro de conexão');return o;
}
const shareLink=()=>location.origin+'/#room='+encodeURIComponent(room)+'&key='+encodeURIComponent(secret);
async function pair(){
 if(!room)return;
 const saved=JSON.parse(sessionStorage.getItem('nl-device-'+room)||'null');
 if(saved && /^[a-f0-9]{32}$/.test(saved.id) && /^[a-f0-9]{64}$/.test(saved.token)){
  devId=saved.id;devToken=saved.token;
  try{await api('/api/messages?after=0');$('#conn').textContent='Dispositivo autorizado';refresh();return}catch{devId='';devToken='';sessionStorage.removeItem('nl-device-'+room)}
 }
 $('#conn').textContent='Solicitando autorização';
 const random=new Uint8Array(32);crypto.getRandomValues(random);
 const proof=Array.from(random,b=>b.toString(16).padStart(2,'0')).join('');
 try{
  const p=await api('/api/pair/start','POST',{name:$('#sender').value||'Navegador',proof});
  $('#conn').textContent='Aprovar código '+p.code+' no servidor';
  toast('Código: '+p.code+' | No computador servidor: bash aprovar.sh '+p.code);
  clearInterval(pairTimer);
  let attempts=0;
  pairTimer=setInterval(async()=>{
   if(room==='' || attempts++>110){clearInterval(pairTimer);$('#conn').textContent='Pareamento expirado';return;}
   try{
    const result=await api('/api/pair/status?id='+encodeURIComponent(p.id),'GET',undefined,{'X-Pair-Proof':proof});
    if(result.status==='approved'){
     clearInterval(pairTimer);devId=result.device_id;devToken=result.token;
     sessionStorage.setItem('nl-device-'+room,JSON.stringify({id:devId,token:devToken}));
     $('#conn').textContent='Autorizado';refresh();timer=setInterval(refresh,4000);toast('Navegador autorizado!');
    }
   }catch(e){$('#conn').textContent='Pareamento: '+e.message;}
  },5000);
 }catch(e){$('#conn').textContent=e.message;toast(e.message)}
}
function connect(r,k){
 if(!/^[a-f0-9]{12}$/.test(r)||!/^[a-f0-9]{48}$/.test(k))throw Error('Convite inválido');
 room=r;secret=k;cursor=0;devId='';devToken='';
 $('#roomName').textContent='#'+room;$('#invite').disabled=false;$('#send').disabled=false;
 $('#stream').replaceChildren();location.hash='room='+room+'&key='+secret;
 clearInterval(timer);clearInterval(pairTimer);pair();
}
async function refresh(){
 if(!room||!devToken)return;
 try{
  const o=await api('/api/messages?after='+cursor);
  for(const m of o.messages){
   cursor=Math.max(cursor,m.id);
   const node=document.createElement('article');node.className='item'+(m.sender===$('#sender').value?' own':'');
   const meta=document.createElement('div');meta.className='meta';meta.textContent=m.sender;
   const t=document.createElement('time');t.textContent=new Date(m.ts*1000).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});meta.append(t);
   const b=document.createElement('div');b.className='body';b.textContent=m.body;node.append(meta,b);$('#stream').append(node);$('#stream').scrollTop=$('#stream').scrollHeight;
  }
  $('#conn').textContent='Conectado';
 }catch(e){$('#conn').textContent=e.message}
}
$('#create').onclick=async()=>{
 if(!['localhost','127.0.0.1'].includes(location.hostname)){toast('Por segurança, crie salas apenas no computador servidor: bash criar_sala.sh');return;}
 const admin=prompt('Criação restrita. Cole o token do arquivo data/admin.token no computador servidor:');
 if(!admin)return;
 try{const o=await api('/api/rooms','POST',{}, {'X-Admin-Token':admin});connect(o.room,o.secret);toast('Sala criada. Aprove seu navegador no terminal!')}
 catch(e){toast(e.message)}
};
$('#join').onclick=()=>$('#modal').showModal();
$('#modalForm').addEventListener('submit',e=>{if(e.submitter?.value==='cancel')return;try{const u=new URL($('#inviteInput').value);if(u.origin!==location.origin)throw Error('Servidor diferente');const p=new URLSearchParams(u.hash.slice(1));connect(p.get('room')||'',p.get('key')||'')}catch{toast('Convite inválido')}});
$('#invite').onclick=()=>navigator.clipboard.writeText(shareLink()).then(()=>toast('Convite copiado')).catch(()=>prompt('Copie o convite',shareLink()));
$('#composer').onsubmit=async e=>{e.preventDefault();if(!devToken){toast('Aguarde autorização deste dispositivo');return}const name=$('#sender').value.trim(),body=$('#message').value.trim();if(!name||!body)return;try{await api('/api/messages','POST',{sender:name,body});$('#message').value='';refresh()}catch(ex){toast(ex.message)}};
$('#sender').value=localStorage.getItem('nucleolink-name')||'Navegador';
$('#sender').onchange=()=>localStorage.setItem('nucleolink-name',$('#sender').value);
(async()=>{try{const o=await api('/api/health');$('#conn').textContent=o.ok?'Servidor disponível':'Indisponível'}catch{$('#conn').textContent='Sem servidor'}const p=new URLSearchParams(location.hash.slice(1));if(p.has('room')&&p.has('key'))try{connect(p.get('room'),p.get('key'))}catch{}})();
