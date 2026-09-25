(()=>{
const $=(s,c=document)=>c.querySelector(s),$$=(s,c=document)=>[...c.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const DB=()=>window.KYLA_DB||null; // web/supabase.js (optional; cloud when signed in, else localStorage)
const dbCall=(fn)=>{try{const d=DB(); if(d) Promise.resolve(fn(d)).catch(()=>{});}catch(_){}};

const weather=[
  {icon:'☼',temp:'22°',state:'soft clouds',range:'H 25° / L 17°'},
  {icon:'☁',temp:'20°',state:'cool + clear',range:'H 24° / L 16°'},
  {icon:'◌',temp:'23°',state:'highland breeze',range:'H 26° / L 18°'}
];
const dateFmt=new Intl.DateTimeFormat('en-KE',{weekday:'long',month:'short',day:'numeric'});
const dateEl=$('#current-date'); if(dateEl) dateEl.textContent=dateFmt.format(new Date());
const w=weather[new Date().getDate()%weather.length];
const wi=$('#weather-icon'),wt=$('#temperature'),ws=$('#weather-state'),wh=$('#weather-high-low');
if(wi)wi.textContent=w.icon; if(wt)wt.textContent=w.temp; if(ws)ws.textContent=w.state; if(wh)wh.textContent=w.range;

$$('[data-view-target]').forEach(b=>b.addEventListener('click',()=>{
  $('#'+b.dataset.viewTarget)?.scrollIntoView({behavior:'smooth',block:'start'});
}));

let activeAgent=(window.KYLA_DEFAULT_AGENT||'ruflo');
let activeRoom=(window.KYLA_DEFAULT_ROOM||'R1');
(()=>{try{
  const q=new URLSearchParams(location.search).get('api');
  if(q){ window.KYLA_API=q; try{localStorage.setItem('KYLA_API',q)}catch(_){}}
  else if(!window.KYLA_API){ const s=localStorage.getItem('KYLA_API'); if(s) window.KYLA_API=s; }
}catch(_){}})();
const apiBase=()=>String(window.KYLA_API||'').trim().replace(/\/$/,'');
const isOnline=()=>!!apiBase();

function setBadge(state,label){
  const el=$('#online-badge'); if(!el) return;
  el.dataset.state=state;
  const span=el.querySelector('span');
  if(span) span.textContent=label;
  const hint=$('#online-hint');
  if(hint){
    hint.textContent=state==='online'
      ? 'Phone ↔ Pages UI · brain = live bridge'
      : 'Phone ↔ Pages UI · brain = bridge host or Actions (see docs/ONLINE.md)';
  }
}

function addMsg(who,text,cls){
  const log=$('#chat-log'); if(!log) return;
  const extra=cls?` ${cls}`:'';
  log.insertAdjacentHTML('beforeend',
    `<div class="message${extra}"><small>${esc(who)}</small><p>${esc(text)}</p></div>`);
  log.lastElementChild.scrollIntoView({behavior:'smooth',block:'nearest'});
}

async function probe(){
  const base=apiBase();
  if(!base){ setBadge('offline','Offline · API not set'); return; }
  setBadge('checking','Checking bridge…');
  try{
    const ctrl=new AbortController();
    const t=setTimeout(()=>ctrl.abort(),6000);
    const r=await fetch(base+'/v1/health',{signal:ctrl.signal});
    clearTimeout(t);
    if(!r.ok) throw new Error('HTTP '+r.status);
    const j=await r.json();
    setBadge('online','Online · '+(j.default_agent||'ruflo')+' bridge');
  }catch(_e){
    setBadge('offline','Bridge unreachable');
  }
}

async function runAgent(prompt){
  const base=apiBase();
  if(!base){
    addMsg('KYLA / offline',
      'Online API not connected. Interactive room bots need the online bridge on an always-on host (Grok Bot box now / VPS later / Melvin Mac localhost later) + free cloudflared tunnel. Scheduled 24/7 agents already run via GitHub Actions with zero Melvin. See docs/ONLINE.md or tap Connect.');
    return;
  }
  addMsg('KYLA / '+activeAgent,'…thinking…','pending');
  const pending=$('#chat-log')?.lastElementChild;
  const started=new Date().toISOString();
  const agent=activeAgent, room=activeRoom;
  const signedIn=!!(DB()&&DB().state().signedIn);
  try{
    const r=await fetch(base+'/v1/run',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      // logged_by_client: the browser writes this run to Supabase itself, so the bridge skips its copy
      body:JSON.stringify({room,agent,prompt,logged_by_client:signedIn})
    });
    const j=await r.json().catch(()=>({ok:false,reply:'Bad JSON from bridge'}));
    if(pending) pending.remove();
    const reply=j.reply||j.error||'(empty reply)';
    addMsg(
      `KYLA / ${j.agent||agent} · ${j.room||room}${j.ms!=null?` · ${j.ms}ms`:''}`,
      reply,
      j.ok===false?'error':''
    );
    dbCall(d=>d.saveChat({room,agent:j.agent||agent,role:'assistant',content:reply}));
    dbCall(d=>d.logRun({agent:j.agent||agent,room:j.room||room,status:j.ok===false?'error':'ok',input:prompt,output:reply,started_at:started,finished_at:new Date().toISOString(),meta:{ms:j.ms??null}}));
  }catch(e){
    if(pending) pending.remove();
    addMsg('KYLA / error','Bridge call failed: '+(e&&e.message||e)+'. Is cloudflared still up?','error');
    dbCall(d=>d.logRun({agent,room,status:'error',input:prompt,output:String(e&&e.message||e),started_at:started,finished_at:new Date().toISOString()}));
  }
}

const context=$('#chat-context');
$$('.room').forEach(card=>card.addEventListener('click',()=>{
  const agent=card.dataset.agent||activeAgent;
  const roomId=card.dataset.room||activeRoom;
  activeAgent=agent; activeRoom=roomId;
  const meta=(window.KYLA_ROOMS&&roomId&&window.KYLA_ROOMS.byId(roomId))||null;
  const live=meta&&(meta.agent==='ruflo'||meta.status==='live')?' · LIVE':'';
  if(context) context.textContent=`${agent} room / ${roomId}${live}`;
  const input=$('#chat-input'); if(input) input.placeholder='Leave a direction for '+agent+'…';
  const line=meta&&window.KYLA_ROOMS.statusLine
    ? window.KYLA_ROOMS.statusLine(meta)
    : (agent+' is ready for a brief.');
  addMsg('KYLA / room opened',
    line+(isOnline()?' Bridge is live — send a prompt.':' Online API not connected — tap Connect.'));
}));

$('#chat-form')?.addEventListener('submit',e=>{
  e.preventDefault();
  const input=$('#chat-input');
  const text=(input?.value||'').trim();
  if(!text) return;
  addMsg('you / now',text,'user');
  if(input) input.value='';
  if(handleSlash(text)) return;
  dbCall(d=>d.saveChat({room:activeRoom,agent:activeAgent,role:'user',content:text}));
  runAgent(text);
});

/* Tasks + notes (Supabase when signed in, localStorage otherwise). /task, /note, /tasks */
function handleSlash(text){
  const m=/^\/(task|note|tasks|help)\b\s*(.*)$/i.exec(text); if(!m) return false;
  const cmd=m[1].toLowerCase(), rest=m[2].trim();
  const d=DB();
  const where=()=>d&&d.state().signedIn?'Supabase':'this browser';
  if(!d){ addMsg('KYLA / tasks','Storage module not loaded — reload the page.','error'); return true; }
  if(cmd==='help'){ addMsg('KYLA / commands','/task <text> — add a task\n/note <text> — save a note\n/tasks — list open tasks (tap one in the focus panel to finish it)'); return true; }
  if(cmd==='tasks'){ renderTasks(true); return true; }
  if(!rest){ addMsg('KYLA / tasks','Usage: /'+cmd+' <text>'); return true; }
  Promise.resolve(d.addTask(rest,cmd,activeRoom)).then(()=>{
    addMsg('KYLA / '+cmd,(cmd==='task'?'Task added':'Note saved')+' → '+where()+'.');
    if(cmd==='task') renderTasks(false);
  }).catch(e=>addMsg('KYLA / '+cmd,'Could not save: '+(e&&e.message||e),'error'));
  return true;
}
async function renderTasks(announce){
  const d=DB(); const list=$('.focus-list'); if(!d) return;
  let tasks=[]; try{ tasks=await d.listTasks({status:'todo',kind:'task',limit:5})||[]; }catch(_){}
  if(announce) addMsg('KYLA / tasks',tasks.length?tasks.map((t,i)=>`${i+1}. ${t.title}`).join('\n'):'No open tasks. Add one with /task <text>.');
  if(!list||!tasks.length) return;
  list.textContent='';
  tasks.slice(0,3).forEach((t,i)=>{
    const row=document.createElement('div');
    row.setAttribute('role','button'); row.tabIndex=0; row.title='Mark done'; row.style.cursor='pointer';
    row.append(String(i+1).padStart(2,'0')+' ');
    const span=document.createElement('span'); span.textContent=t.title; row.appendChild(span);
    const done=()=>{ Promise.resolve(d.setTaskStatus(t.id,'done')).then(()=>{row.classList.add('done');row.firstChild.textContent='✓ ';setTimeout(()=>renderTasks(false),600);}); };
    row.addEventListener('click',done);
    row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();done();}});
    list.appendChild(row);
  });
}
let historyLoaded=false;
async function loadHistory(){
  const d=DB(); if(!d||historyLoaded) return;
  const s=d.state(); if(!s.signedIn) return;
  historyLoaded=true;
  try{
    const rows=await d.recentChats(10)||[];
    if(rows.length){
      addMsg('KYLA / history','Last '+rows.length+' messages from Supabase:');
      rows.forEach(r=>addMsg((r.role==='user'?'you':'KYLA / '+(r.agent||'kyla'))+' / earlier',r.content,r.role==='user'?'user':''));
    }
  }catch(_){}
}
window.addEventListener('kyla:db',e=>{ const s=e.detail||{}; if(s.ready){ renderTasks(false); loadHistory(); } if(!s.signedIn) historyLoaded=false; });

const focuses=[
  ['Build the quiet version','A small, finished surface beats a perfect system waiting backstage.'],
  ['Name the real signal','If it matters, make it visible before making it clever.'],
  ['Protect the first hour','Give the next clear move a clean room to land in.']
];
let focus=0;
$('#shuffle-focus')?.addEventListener('click',()=>{
  focus=(focus+1)%focuses.length;
  const t=$('#focus-title'),c=$('#focus-copy');
  if(t) t.textContent=focuses[focus][0];
  if(c) c.textContent=focuses[focus][1];
});
$('#focus-toggle')?.addEventListener('click',e=>{
  document.body.classList.toggle('focus-mode');
  e.currentTarget.setAttribute('aria-pressed',document.body.classList.contains('focus-mode'));
});

const panel=$('.scene-card')||$('[data-scene-url]');
const url=(panel&&(panel.dataset.sceneUrl||'')).trim();
if(url){
  const frame=$('#astra-frame'); if(frame) frame.src=url;
  $('#scene-viewport')?.classList.add('has-scene');
}

$('#connect-help')?.addEventListener('click',()=>{
  addMsg('KYLA / how to go online',
    'INTERACTIVE (needs always-on host):\n1) python tools/online_bridge.py\n2) cloudflared tunnel --url http://127.0.0.1:8787\n3) Open Pages with ?api=YOUR_TUNNEL_URL (or set web/config.js)\n4) Reload — phone remembers api in localStorage.\n\nSCHEDULED 24/7 (zero Melvin):\nGitHub Actions crons — daily brief, stack-health, repo-digest, ruflo-health. No laptop required.\n\nLater: point KYLA_API at localhost when Mac is ready.\nFull guide: docs/ONLINE.md');
});

probe();
setInterval(probe,60000);
if(DB()&&DB().state().ready){ renderTasks(false); loadHistory(); }
})();
