/* KYLA × Supabase — optional cloud sync + magic-link login for the static UI.
 *
 * No build step. supabase-js is loaded lazily from a CDN (ESM via dynamic import)
 * ONLY when a Project URL + anon/publishable key are configured, so nothing is
 * downloaded and nothing breaks before the Supabase project exists.
 *
 * Config (first match wins):
 *   1. localStorage (set from the Account panel → "Supabase settings")
 *   2. web/config.js → window.KYLA_SUPABASE_URL / window.KYLA_SUPABASE_ANON_KEY
 *
 * The anon / publishable key is public-safe (Row Level Security protects data).
 * The service_role / sb_secret_ key must NEVER be put here — it is rejected.
 *
 * Exposes window.KYLA_DB (always defined; falls back to localStorage).
 */
(()=>{
'use strict';
const LS_URL='KYLA_SUPABASE_URL', LS_KEY='KYLA_SUPABASE_ANON_KEY', LS_DATA='KYLA_LOCAL_DATA_V1';
const CDNS=[
  'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm',
  'https://esm.sh/@supabase/supabase-js@2'
];
const CAP={chats:200,runs:100,tasks:200};
const $=s=>document.querySelector(s);
const lsGet=k=>{try{return localStorage.getItem(k)||''}catch(_){return ''}};
const lsSet=(k,v)=>{try{v?localStorage.setItem(k,v):localStorage.removeItem(k)}catch(_){}};
const nowIso=()=>new Date().toISOString();
const clip=(s,n=20000)=>{s=String(s??'');return s.length>n?s.slice(0,n)+'\n…[truncated]':s};

function cfg(){
  const url=(lsGet(LS_URL)||window.KYLA_SUPABASE_URL||'').trim().replace(/\/$/,'');
  const key=(lsGet(LS_KEY)||window.KYLA_SUPABASE_ANON_KEY||'').trim();
  return {url,key};
}
/* Returns a reason string if the key must not be used in the browser. */
function keyProblem(key){
  if(!key) return 'missing key';
  if(/^sb_secret_/i.test(key)) return 'That is a SECRET key. Use the anon / publishable key in the browser.';
  if(/^eyJ/.test(key)){
    try{
      const b=key.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');
      const p=JSON.parse(atob(b+'==='.slice((b.length+3)%4)));
      if(p&&p.role==='service_role') return 'That is the service_role key. Use the anon key in the browser.';
    }catch(_){}
  }
  return '';
}
function validUrl(u){return /^https:\/\/[^\s/]+/.test(u)||/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?/.test(u)}

/* ---------- local fallback store ---------- */
function loadLocal(){
  try{const d=JSON.parse(lsGet(LS_DATA)||'{}');return {chats:d.chats||[],runs:d.runs||[],tasks:d.tasks||[],memories:d.memories||{}}}
  catch(_){return {chats:[],runs:[],tasks:[],memories:{}}}
}
function saveLocal(d){
  d.chats=d.chats.slice(-CAP.chats); d.runs=d.runs.slice(-CAP.runs); d.tasks=d.tasks.slice(-CAP.tasks);
  try{localStorage.setItem(LS_DATA,JSON.stringify(d))}catch(_){}
}
const local={
  add(kind,row){const d=loadLocal();row={id:'l_'+Date.now().toString(36)+Math.random().toString(36).slice(2,6),created_at:nowIso(),...row};d[kind].push(row);saveLocal(d);return row},
  list(kind,limit){return loadLocal()[kind].slice(-limit).reverse()},
  update(kind,id,patch){const d=loadLocal();const r=d[kind].find(x=>x.id===id);if(r)Object.assign(r,patch,{updated_at:nowIso()});saveLocal(d);return r||null}
};

/* ---------- cloud client (lazy) ---------- */
let sb=null, session=null, lastError='', loading=null;
const st={configured:false,ready:false};

function emit(){
  const s=api.state();
  try{window.dispatchEvent(new CustomEvent('kyla:db',{detail:s}))}catch(_){}
  renderAccount(s);
}
async function importSdk(){
  for(const u of CDNS){
    try{const m=await import(u); if(m&&m.createClient) return m;}catch(e){lastError='CDN blocked: '+u}
  }
  throw new Error('Could not load supabase-js from CDN');
}
function init(){
  if(loading) return loading;
  const {url,key}=cfg();
  const bad=keyProblem(key);
  st.configured=!!(url&&key&&validUrl(url)&&!bad);
  if(url&&key&&bad) lastError=bad;
  if(!st.configured){ st.ready=true; emit(); return (loading=Promise.resolve(null)); }
  loading=(async()=>{
    try{
      const {createClient}=await importSdk();
      sb=createClient(url,key,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storageKey:'kyla-auth'}});
      const {data}=await sb.auth.getSession();
      session=data&&data.session||null;
      sb.auth.onAuthStateChange((_evt,s)=>{session=s||null;emit();});
      lastError='';
    }catch(e){ sb=null; lastError=String(e&&e.message||e); }
    st.ready=true; emit(); return sb;
  })();
  return loading;
}
const cloud=()=>!!(sb&&session&&session.user);
const uid=()=>session&&session.user&&session.user.id;

async function tryCloud(fn,fallback,label){
  if(!cloud()) return fallback();
  try{const {data,error}=await fn(sb); if(error) throw error; return data;}
  catch(e){console.warn('[KYLA_DB] '+label+' → local fallback:',e&&e.message||e); lastError=String(e&&e.message||e); return fallback();}
}

const api={
  state(){
    const u=session&&session.user;
    return {configured:st.configured,ready:st.ready,signedIn:!!u,email:u&&u.email||'',mode:cloud()?'cloud':'local',error:lastError};
  },
  ready:()=>init(),
  keyProblem,
  saveSettings(url,key){
    url=String(url||'').trim().replace(/\/$/,''); key=String(key||'').trim();
    if(url&&!validUrl(url)) return {ok:false,error:'Project URL should look like https://xxxx.supabase.co'};
    const bad=key&&keyProblem(key); if(bad) return {ok:false,error:bad};
    lsSet(LS_URL,url); lsSet(LS_KEY,key); return {ok:true};
  },
  clearSettings(){lsSet(LS_URL,'');lsSet(LS_KEY,'');},
  async signIn(email){
    await init();
    if(!sb) return {ok:false,error:st.configured?(lastError||'Supabase unavailable'):'Supabase not configured yet — add URL + anon key in settings.'};
    const redirect=location.origin+location.pathname;
    const {error}=await sb.auth.signInWithOtp({email:String(email||'').trim(),options:{emailRedirectTo:redirect}});
    return error?{ok:false,error:error.message}:{ok:true};
  },
  async signOut(){ if(sb){try{await sb.auth.signOut()}catch(_){}} session=null; emit(); },

  /* chats */
  saveChat({room,agent,role,content}){
    const row={room:room||null,agent:agent||null,role:role||'user',content:clip(content,8000)};
    return tryCloud(c=>c.from('chat_messages').insert({...row,user_id:uid()}),()=>local.add('chats',row),'saveChat');
  },
  recentChats(limit=12){
    return tryCloud(async c=>{const r=await c.from('chat_messages').select('room,agent,role,content,created_at').order('created_at',{ascending:false}).limit(limit);return r;},
      ()=>local.list('chats',limit),'recentChats').then(x=>(x||[]).slice().reverse());
  },
  /* agent runs */
  logRun({agent,room,status,input,output,started_at,finished_at,meta}){
    const row={agent:agent||'unknown',room:room||null,status:status||'ok',input:clip(input),output:clip(output),source:'web',
      started_at:started_at||nowIso(),finished_at:finished_at||nowIso(),meta:meta||{}};
    return tryCloud(c=>c.from('agent_runs').insert({...row,user_id:uid()}),()=>local.add('runs',row),'logRun');
  },
  recentRuns(limit=8){
    return tryCloud(c=>c.from('agent_runs').select('agent,room,status,source,started_at,finished_at,input').order('started_at',{ascending:false}).limit(limit),
      ()=>local.list('runs',limit),'recentRuns');
  },
  /* tasks + notes */
  addTask(title,kind='task',room=null){
    const row={title:clip(title,500),kind,status:'todo',room};
    return tryCloud(async c=>c.from('tasks').insert({...row,user_id:uid()}).select().single(),()=>local.add('tasks',row),'addTask');
  },
  listTasks({status='todo',kind='task',limit=5}={}){
    return tryCloud(c=>{let q=c.from('tasks').select('id,title,kind,status,room,created_at').eq('kind',kind).order('created_at',{ascending:false}).limit(limit);if(status)q=q.eq('status',status);return q;},
      ()=>local.list('tasks',CAP.tasks).filter(t=>t.kind===kind&&(!status||t.status===status)).slice(0,limit),'listTasks');
  },
  setTaskStatus(id,status){
    if(String(id).startsWith('l_')) return Promise.resolve(local.update('tasks',id,{status}));
    return tryCloud(c=>c.from('tasks').update({status}).eq('id',id),()=>local.update('tasks',id,{status}),'setTaskStatus');
  },
  /* memories (key/value) */
  remember(key,value){
    return tryCloud(c=>c.from('memories').upsert({user_id:uid(),key,value},{onConflict:'user_id,key'}),
      ()=>{const d=loadLocal();d.memories[key]=value;saveLocal(d);return {key,value};},'remember');
  }
};
window.KYLA_DB=api;

/* ---------- Account panel UI (markup lives in index.html) ---------- */
function renderAccount(s){
  const btn=$('#account-btn'); if(!btn) return;
  const label=btn.querySelector('span');
  btn.dataset.state=s.signedIn?'cloud':(s.configured?'ready':'local');
  if(label) label.textContent=s.signedIn?(s.email.split('@')[0]||'signed in'):(s.configured?'sign in':'local');
  btn.title=s.signedIn?'Synced to Supabase as '+s.email:(s.configured?'Supabase ready — sign in to sync':'Local mode — history stays on this device');
  const status=$('#account-status');
  if(status){
    status.textContent=s.signedIn
      ?'Signed in · chats, tasks and runs sync to Supabase.'
      :s.configured
        ?(s.ready?'Supabase connected. Sign in with a magic link to sync.':'Connecting to Supabase…')
        :'Local mode · history stays in this browser. Add your Supabase URL + anon key below to enable cloud sync.';
    if(s.error) status.textContent+=' ('+s.error+')';
  }
  const login=$('#account-login'), signed=$('#account-signed');
  if(login) login.hidden=!!s.signedIn;
  if(signed) signed.hidden=!s.signedIn;
  const who=$('#account-who'); if(who) who.textContent=s.email;
  const det=$('.account-settings'); if(det&&!s.configured) det.open=true; // show settings until configured
  const {url,key}=cfg(); const u=$('#sb-url'), k=$('#sb-key');
  if(u&&!u.value) u.value=url; if(k&&!k.value) k.value=key;
}
async function renderRuns(){
  const ol=$('#account-runs'); if(!ol) return;
  const runs=await api.recentRuns(6);
  ol.textContent='';
  if(!runs||!runs.length){const li=document.createElement('li');li.textContent='No runs yet.';ol.appendChild(li);return;}
  for(const r of runs){
    const li=document.createElement('li');
    const t=r.started_at?new Date(r.started_at).toLocaleString('en-KE',{hour:'2-digit',minute:'2-digit',month:'short',day:'numeric'}):'';
    li.textContent=`${r.agent||'?'} · ${r.status||''} · ${r.source||'web'} · ${t}`;
    ol.appendChild(li);
  }
}
function bindAccount(){
  const panel=$('#account-panel'), btn=$('#account-btn');
  if(!panel||!btn) return;
  const msg=(t)=>{const s=$('#account-msg'); if(s) s.textContent=t||'';};
  btn.addEventListener('click',()=>{panel.hidden=!panel.hidden; if(!panel.hidden){renderRuns();}});
  $('#account-close')?.addEventListener('click',()=>{panel.hidden=true;});
  $('#account-login')?.addEventListener('submit',async e=>{
    e.preventDefault();
    const email=($('#account-email')?.value||'').trim();
    if(!email){msg('Enter your email.');return;}
    msg('Sending magic link…');
    const r=await api.signIn(email);
    msg(r.ok?'Check your inbox for the KYLA login link (open it on this device).':('Could not send: '+r.error));
  });
  $('#account-logout')?.addEventListener('click',async()=>{await api.signOut();msg('Signed out. Local mode.');});
  $('#sb-save')?.addEventListener('click',()=>{
    const r=api.saveSettings($('#sb-url')?.value,$('#sb-key')?.value);
    if(!r.ok){msg(r.error);return;}
    msg('Saved. Reloading…'); setTimeout(()=>location.reload(),400);
  });
  $('#sb-clear')?.addEventListener('click',()=>{api.clearSettings();msg('Cleared. Reloading…');setTimeout(()=>location.reload(),400);});
  window.addEventListener('kyla:db',()=>{if(!panel.hidden) renderRuns();});
}

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>{bindAccount();init();});
else {bindAccount();init();}
})();
