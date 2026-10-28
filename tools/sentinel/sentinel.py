#!/usr/bin/env python3
"""Sentinel desktop helper for XFCE/X11."""
import argparse, base64, datetime as dt, json, logging, logging.handlers, os, shutil, signal, socket, sqlite3, subprocess, sys, threading
from pathlib import Path

HERE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'sentinel'
LOGS=DATA/'logs'; SHOTS=DATA/'screenshots'; DB=DATA/'reminders.sqlite3'; LIMIT=500*1024*1024
PROVIDERS={'anthropic':('ANTHROPIC_API_KEY','claude-sonnet-4-5-20250929'),'openai':('OPENAI_API_KEY','gpt-4o-mini'),'gemini':('GEMINI_API_KEY','gemini-2.5-flash')}
def envfile():
 try:
  for line in (HERE/'.env').read_text().splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('\"\''))
 except OSError: pass
def provider():
 envfile(); p=os.getenv('SENTINEL_PROVIDER','anthropic').lower()
 try: p=os.getenv('SENTINEL_PROVIDER',json.loads((Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'sentinel/settings.json').read_text()).get('provider',p)).lower()
 except (OSError,ValueError,AttributeError): pass
 return p if p in PROVIDERS else 'anthropic'
def self_check():
 envfile(); results=[]
 try:
  import gi,requests,mss
  gi.require_version('Gtk','3.0'); from gi.repository import Gtk,Gdk,GLib
  results.append((1,'dependency imports','GTK 3, requests, mss imported','Run ./setup.sh to install dependencies.'))
 except Exception as e: results.append((0,'dependency imports',str(e),'Run ./setup.sh to install GTK/Python dependencies.'))
 sess=os.getenv('XDG_SESSION_TYPE','').lower(); disp=os.getenv('DISPLAY','')
 try: xok=bool(disp) and sess!='wayland' and subprocess.run(['xset','-q'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3).returncode==0
 except (OSError,subprocess.TimeoutExpired): xok=False
 results.append((xok,'DISPLAY / X11',f'DISPLAY={disp or "unset"}; session={sess or "unspecified"}','Log in to an XFCE X11 session; Wayland is unsupported.'))
 avail=all(shutil.which(x) for x in ('xset','xprintidle')); results.append((avail,'xset + xprintidle','both available' if avail else 'one or both missing','Install x11-xserver-utils and xprintidle with apt.'))
 p=provider(); key=PROVIDERS[p][0]; ok=bool(os.getenv(key,'').strip()); results.append((ok,'provider API key',f'{p}: {key} '+('configured' if ok else 'missing'),f'Set {key} in tools/sentinel/.env and match SENTINEL_PROVIDER.'))
 try:
  DATA.mkdir(parents=True,exist_ok=True)
  with sqlite3.connect(DB) as d: d.execute('CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY,title TEXT NOT NULL,due_at TEXT NOT NULL,created_at TEXT NOT NULL,notified INTEGER NOT NULL DEFAULT 0)'); d.execute('SELECT 1')
  results.append((1,'SQLite open',str(DB),'Check XDG_DATA_HOME permissions and free space.'))
 except Exception as e: results.append((0,'SQLite open',str(e),'Check XDG_DATA_HOME permissions and free space.'))
 try:
  LOGS.mkdir(parents=True,exist_ok=True); (LOGS/'sentinel.log').open('a').close(); results.append((1,'log writable',str(LOGS/'sentinel.log'),'Check log directory permissions and free space.'))
 except Exception as e: results.append((0,'log writable',str(e),'Check log directory permissions and free space.'))
 for ok,n,d,h in results: print(f"{'PASS' if ok else 'FAIL'} | {n} | {d} | Fix: {h}")
 return 0 if all(x[0] for x in results) else 1

def sockpath(): return Path(os.getenv('XDG_RUNTIME_DIR','/tmp'))/f'sentinel-{os.getuid()}.sock'
class App:
 def __init__(self):
  import gi
  gi.require_version('Gtk','3.0'); from gi.repository import Gtk,GLib
  self.Gtk,self.GLib=Gtk,GLib; DATA.mkdir(parents=True,exist_ok=True); LOGS.mkdir(exist_ok=True); SHOTS.mkdir(exist_ok=True)
  self.logger=logging.getLogger('sentinel'); self.logger.setLevel(logging.INFO); self.logger.propagate=False
  h=logging.handlers.RotatingFileHandler(LOGS/'sentinel.log',maxBytes=8*1024*1024,backupCount=4); self.logger.addHandler(h)
  self.settings={'provider':provider(),'model':'','keep_screenshots':False}; self.paused=False; self.window=None
  try: self.settings.update(json.loads((Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'sentinel/settings.json').read_text()))
  except (OSError,ValueError): pass
  with sqlite3.connect(DB) as d: d.execute('CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY,title TEXT NOT NULL,due_at TEXT NOT NULL,created_at TEXT NOT NULL,notified INTEGER NOT NULL DEFAULT 0)')
  self.tray=Gtk.StatusIcon.new_from_icon_name('dialog-information'); self.tray.set_tooltip_text('Sentinel'); self.tray.set_visible(True); self.tray.connect('activate',lambda *_:self.ask('capture'))
  self.tray.connect('popup-menu',self.menu); self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); self.server_path=sockpath(); self.server_path.parent.mkdir(parents=True,exist_ok=True); self.server_path.unlink(missing_ok=True); self.server.bind(str(self.server_path)); os.chmod(self.server_path,0o600); self.server.listen(8); self.server.setblocking(False); GLib.io_add_watch(self.server,GLib.IO_IN,self.ipc)
  GLib.timeout_add_seconds(30,self.reminder_tick); GLib.timeout_add_seconds(60,self.prune); self.log('started',{})
 def log(self,event,data):
  self.logger.info(json.dumps({'time':dt.datetime.now().astimezone().isoformat(),'event':event,'data':data},default=str)); self.prune()
 def prune(self):
  files=[]
  for root in (LOGS,SHOTS):
   if root.exists():
    for f in root.rglob('*'):
     try:
      if f.is_file(): files.append((f.stat().st_mtime,f,f.stat().st_size))
     except OSError: pass
  total=sum(x[2] for x in files); active=LOGS/'sentinel.log'
  for _,f,size in sorted(files):
   if total<=LIMIT: break
   if f==active: continue
   try: f.unlink(); total-=size
   except OSError: pass
  return True
 def menu(self,*args):
  G=self.Gtk; m=G.Menu()
  for title,fn in [('Ask about screen',lambda:self.ask('capture')),('Plan actions',lambda:self.ask('plan')),('Add reminder',self.reminder_dialog),('Settings',self.settings_dialog),('View logs',self.show_logs),('Pause / resume',self.toggle_pause),('Quit',lambda:G.main_quit())]:
   i=G.MenuItem(label=title); i.connect('activate',lambda _,f=fn:f()); m.append(i)
  m.show_all(); m.popup_at_pointer(None)
 def dialog(self,title,hint=''):
  G=self.Gtk; d=G.Dialog(title=title,flags=G.DialogFlags.MODAL); d.add_button('Cancel',G.ResponseType.CANCEL); d.add_button('Submit',G.ResponseType.OK); e=G.Entry(); e.set_placeholder_text(hint); e.set_activates_default(True); d.get_content_area().pack_start(e,True,True,12); d.set_default_response(G.ResponseType.OK); d.show_all(); r=d.run(); text=e.get_text().strip(); d.destroy(); return text if r==G.ResponseType.OK else None
 def ask(self,mode):
  if self.paused: return
  text=self.dialog('Sentinel: '+mode,'Describe what you need help with')
  if text is not None: threading.Thread(target=self.ask_worker,args=(mode,text),daemon=True).start()
 def ask_worker(self,mode,text):
  try:
   image=None
   if mode=='capture':
    import mss
    with mss.mss() as s: image=base64.b64encode(mss.tools.to_png(s.grab(s.monitors[0]).rgb,s.grab(s.monitors[0]).size)).decode()
    if self.settings.get('keep_screenshots'):
     (SHOTS/(dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'.png')).write_bytes(base64.b64decode(image)); self.prune()
   answer=self.call(text,image); self.log('response',{'mode':mode})
   self.GLib.idle_add(self.message,answer)
  except Exception as e: self.log('request_error',{'error':str(e)}); self.GLib.idle_add(self.message,'Request failed: '+str(e))
 def call(self,text,image=None,reminder=False):
  import requests
  p=self.settings.get('provider','anthropic'); keyname,default=PROVIDERS.get(p,PROVIDERS['anthropic']); key=os.getenv(keyname,'').strip()
  if not key: raise RuntimeError('Missing '+keyname+' in .env')
  model=self.settings.get('model') or default
  if reminder: text='Interpret this natural-language reminder relative to local current time '+dt.datetime.now().astimezone().isoformat()+'. Return ONLY JSON: {"title":"short reminder","due_at":"ISO-8601 datetime including timezone"}. Reminder: '+text
  if p=='anthropic':
   parts=[{'type':'text','text':text}]
   if image: parts.append({'type':'image','source':{'type':'base64','media_type':'image/png','data':image}})
   r=requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':key,'anthropic-version':'2023-06-01'},json={'model':model,'max_tokens':1200,'messages':[{'role':'user','content':parts}]},timeout=100); r.raise_for_status(); out=''.join(x.get('text','') for x in r.json().get('content',[]))
  elif p=='openai':
   content=[{'type':'text','text':text}]
   if image: content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+image}})
   r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':model,'messages':[{'role':'user','content':content}]},timeout=100); r.raise_for_status(); out=r.json()['choices'][0]['message']['content']
  else:
   parts=[{'text':text}]
   if image: parts.append({'inline_data':{'mime_type':'image/png','data':image}})
   r=requests.post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',headers={'x-goog-api-key':key},json={'contents':[{'parts':parts}]},timeout=100); r.raise_for_status(); out=r.json()['candidates'][0]['content']['parts'][0]['text']
  if reminder:
   data=json.loads(out); due=dt.datetime.fromisoformat(data['due_at'].replace('Z','+00:00'))
   if due.tzinfo is None: due=due.astimezone()
   if not str(data.get('title','')).strip(): raise ValueError('Reminder title is empty')
   with sqlite3.connect(DB) as d: d.execute('INSERT INTO reminders(title,due_at,created_at) VALUES(?,?,?)',(str(data['title']).strip(),due.isoformat(),dt.datetime.now().astimezone().isoformat()))
   return 'Saved reminder: '+data['title']+' — '+due.astimezone().strftime('%Y-%m-%d %H:%M %Z')
  return out
 def reminder_dialog(self):
  text=self.dialog('Add reminder','e.g. call Sam tomorrow at 9am')
  if text: threading.Thread(target=self.reminder_worker,args=(text,),daemon=True).start()
 def reminder_worker(self,text):
  try: msg=self.call(text,reminder=True)
  except Exception as e: msg='Could not save reminder: '+str(e)
  self.GLib.idle_add(self.message,msg)
 def reminder_tick(self):
  try:
   now=dt.datetime.now().astimezone()
   with sqlite3.connect(DB) as d:
    for ident,title,due in d.execute('SELECT id,title,due_at FROM reminders WHERE notified=0').fetchall():
     when=dt.datetime.fromisoformat(due)
     if when.tzinfo is None: when=when.astimezone()
     if when<=now:
      subprocess.run(['notify-send','Sentinel reminder',title],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5); d.execute('UPDATE reminders SET notified=1 WHERE id=?',(ident,)); self.log('reminder_due',{'id':ident,'title':title})
  except Exception as e: self.log('reminder_error',{'error':str(e)})
  return True
 def message(self,text):
  d=self.Gtk.MessageDialog(message_type=self.Gtk.MessageType.INFO,buttons=self.Gtk.ButtonsType.OK,text=str(text)); d.run(); d.destroy(); return False
 def settings_dialog(self):
  p=self.dialog('Provider (anthropic/openai/gemini)',self.settings.get('provider','anthropic'))
  if p and p.lower() in PROVIDERS: self.settings['provider']=p.lower()
  m=self.dialog('Model override (blank uses provider default)',self.settings.get('model',''))
  if m is not None: self.settings['model']=m
  self.config_dir=Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'sentinel'; self.config_dir.mkdir(parents=True,exist_ok=True); (self.config_dir/'settings.json').write_text(json.dumps(self.settings,indent=2)+'\n'); self.message('Settings saved. API keys are read from .env.')
 def show_logs(self):
  try: text=(LOGS/'sentinel.log').read_text(errors='replace')[-30000:]
  except OSError: text='No log entries.'
  self.message(text)
 def toggle_pause(self): self.paused=not self.paused; self.message('Paused' if self.paused else 'Resumed')
 def ipc(self,source,condition):
  try:
   c,_=source.accept(); raw=c.recv(8192); c.close(); r=json.loads(raw.decode().splitlines()[0]); a=r.get('action')
   if a=='capture': self.ask('capture')
   elif a=='plan': self.ask('plan')
   elif a=='remind': self.reminder_dialog() if not r.get('text') else threading.Thread(target=self.reminder_worker,args=(r['text'],),daemon=True).start()
   elif a=='settings': self.settings_dialog()
   elif a=='logs': self.show_logs()
   elif a=='pause': self.toggle_pause()
   elif a=='quit': self.Gtk.main_quit()
  except Exception as e: self.log('ipc_error',{'error':str(e)})
  return True

def send(action,text=None):
 p=sockpath()
 for attempt in range(2):
  try:
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c: c.settimeout(2); c.connect(str(p)); c.sendall((json.dumps({'action':action,'text':text})+'\n').encode()); return 0
  except OSError:
   if attempt==0:
    subprocess.Popen([sys.executable,str(HERE/'sentinel.py'),'--daemon'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    import time; time.sleep(1)
 return 1

def main():
 p=argparse.ArgumentParser(); p.add_argument('--self-check',action='store_true'); p.add_argument('--daemon',action='store_true'); p.add_argument('--capture',action='store_true'); p.add_argument('--plan',action='store_true'); p.add_argument('--settings',action='store_true'); p.add_argument('--logs',action='store_true'); p.add_argument('--pause',action='store_true'); p.add_argument('--quit',action='store_true'); p.add_argument('--remind',nargs='?',const='',default=None); a=p.parse_args()
 if a.self_check: return self_check()
 action='capture' if a.capture else 'plan' if a.plan else 'settings' if a.settings else 'logs' if a.logs else 'pause' if a.pause else 'quit' if a.quit else 'remind' if a.remind is not None else None
 if action and not a.daemon: return send(action,a.remind)
 try:
  app=App(); signal.signal(signal.SIGTERM,lambda *_:app.GLib.idle_add(app.Gtk.main_quit)); app.Gtk.main()
 finally:
  try: app.server.close(); app.server_path.unlink(missing_ok=True)
  except Exception: pass
 return 0
if __name__=='__main__': sys.exit(main())
