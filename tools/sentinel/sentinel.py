#!/usr/bin/env python3
"""Sentinel GTK3 screen-aware assistant for Linux Mint/Xfce/X11."""
import argparse, base64, datetime as dt, json, logging, logging.handlers, os, re, shutil, signal, sqlite3, subprocess, sys, tempfile, threading
from pathlib import Path
from urllib.parse import quote
HERE=Path(__file__).resolve().parent
DATA=Path(os.getenv('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'sentinel'
LOGS=DATA/'logs'; SHOTS=DATA/'screenshots'; DB=DATA/'reminders.sqlite3'
CAP=500*1024*1024; DEFAULT_PROMPT='Describe what is visible on my screen and point out anything that may need attention.'
MODELS={'gemini':'gemini-2.5-flash','anthropic':'claude-sonnet-4-5-20250929','openai':'gpt-4o-mini'}
def envload():
 try:
  for line in (HERE/'.env').read_text(encoding='utf-8').splitlines():
   line=line.strip()
   if not line or line.startswith('#') or '=' not in line: continue
   k,v=line.split('=',1); k=k.strip(); v=v.strip()
   if len(v)>1 and v[0]==v[-1] and v[0] in '\"\'': v=v[1:-1]
   if k and not k.startswith('#'): os.environ.setdefault(k,v)
 except OSError: pass
def cfg():
 envload(); p=os.getenv('SENTINEL_PROVIDER','gemini').strip().lower()
 if p not in MODELS: p='gemini'
 mk={'gemini':'GEMINI_MODEL','anthropic':'ANTHROPIC_MODEL','openai':'OPENAI_MODEL'}[p]
 return {'provider':p,'model':os.getenv(mk,MODELS[p]).strip() or MODELS[p], 'scope':os.getenv('SENTINEL_SCOPE','full').lower().strip(),'target':os.getenv('SENTINEL_TARGET_WINDOW','').strip(),'tts':os.getenv('TTS_ENGINE','espeak-ng').lower().strip(),'voice':os.getenv('PIPER_VOICE','').strip()}
def dirs():
 for p in (DATA,LOGS,SHOTS): p.mkdir(parents=True,exist_ok=True)
def prune():
 dirs(); fs=[]
 for root in (LOGS,SHOTS):
  for f in root.iterdir():
   try:
    if f.is_file(): fs.append((f.stat().st_mtime,f,f.stat().st_size))
   except OSError: pass
 total=sum(x[2] for x in fs)
 for _,f,n in sorted(fs):
  if total<=CAP: break
  if f==LOGS/'sentinel.log': continue
  try: f.unlink(); total-=n
  except OSError: pass
 return total<=CAP
def logger():
 dirs(); l=logging.getLogger('sentinel')
 if not l.handlers:
  h=logging.handlers.RotatingFileHandler(LOGS/'sentinel.log',maxBytes=8*1024*1024,backupCount=4,encoding='utf-8'); h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s')); l.addHandler(h); l.setLevel(logging.INFO); l.propagate=False
 return l
def dbinit():
 dirs()
 with sqlite3.connect(DB) as d: d.execute('CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY,title TEXT NOT NULL,due_at TEXT NOT NULL,created_at TEXT NOT NULL,notified INTEGER NOT NULL DEFAULT 0)')
def key_for(p=None):
 envload(); p=p or cfg()['provider']; kname={'gemini':'GEMINI_API_KEY','anthropic':'ANTHROPIC_API_KEY','openai':'OPENAI_API_KEY'}[p]; k=os.getenv(kname,'').strip()
 if not k: raise RuntimeError(f'Missing {kname} in tools/sentinel/.env')
 return k
def bodytext(r,p):
 try: b=r.json()
 except ValueError: b=r.text
 if not r.ok: raise RuntimeError(f'{p.title()} API error (HTTP {r.status_code}): {b}')
 try:
  if p=='gemini': return ''.join(x.get('text','') for c in b.get('candidates',[]) for x in c.get('content',{}).get('parts',[]) if x.get('text'))
  if p=='anthropic': return ''.join(x.get('text','') for x in b.get('content',[]) if x.get('type')=='text')
  return b['choices'][0]['message']['content']
 except (KeyError,IndexError,TypeError) as e: raise RuntimeError(f'{p.title()} API returned no usable text: {b}') from e
def gemini(prompt,image=None,audio=None,mime='image/png',model=None):
 import requests
 model=model or os.getenv('GEMINI_MODEL',MODELS['gemini']); parts=[{'text':prompt}]
 if image is not None: parts.append({'inline_data':{'mime_type':mime,'data':image}})
 if audio is not None: parts.append({'inline_data':{'mime_type':'audio/wav','data':audio}})
 url='https://generativelanguage.googleapis.com/v1beta/models/'+quote(model,safe='')+':generateContent'
 r=requests.post(url,headers={'x-goog-api-key':key_for('gemini')},json={'contents':[{'parts':parts}]},timeout=120); return bodytext(r,'gemini')
def ask(prompt,image,mime='image/png'):
 import requests
 c=cfg(); p,m=c['provider'],c['model']; k=key_for(p)
 if p=='gemini': return gemini(prompt,image,mime=mime,model=m)
 if p=='anthropic':
  parts=[{'type':'text','text':prompt}]
  if image: parts.append({'type':'image','source':{'type':'base64','media_type':mime,'data':image}})
  r=requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':k,'anthropic-version':'2023-06-01'},json={'model':m,'max_tokens':1600,'messages':[{'role':'user','content':parts}]},timeout=120)
 else:
  parts=[{'type':'text','text':prompt}]
  if image: parts.append({'type':'image_url','image_url':{'url':f'data:{mime};base64,{image}'}})
  r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+k},json={'model':m,'messages':[{'role':'user','content':parts}]},timeout=120)
 return bodytext(r,p)
def transcribe(a): return gemini('Transcribe the spoken audio exactly. Return only the transcription, without commentary.',audio=a)
def region():
 c=cfg()
 if c['scope']!='window': return None
 title=c['target']
 if not title: raise RuntimeError('SENTINEL_SCOPE is window but SENTINEL_TARGET_WINDOW is empty.')
 r=subprocess.run(['xdotool','search','--name',title],capture_output=True,text=True,timeout=8); ids=r.stdout.splitlines()
 if r.returncode or not ids: raise RuntimeError(f'No window matched SENTINEL_TARGET_WINDOW title: {title!r}')
 r=subprocess.run(['xwininfo','-id',ids[0].strip()],capture_output=True,text=True,timeout=8)
 if r.returncode: raise RuntimeError(f'Could not read bounds for window title {title!r}: {r.stderr.strip() or r.stdout.strip()}')
 v={}
 for k in ('Absolute upper-left X','Absolute upper-left Y','Width','Height'):
  m=re.search(r'^\s*'+re.escape(k)+r':\s*(-?\d+)',r.stdout,re.M)
  if not m: raise RuntimeError(f'Could not determine {k} for window title {title!r}.')
  v[k]=int(m.group(1))
 if v['Width']<1 or v['Height']<1: raise RuntimeError(f'Window title {title!r} has invalid bounds.')
 return {'left':v['Absolute upper-left X'],'top':v['Absolute upper-left Y'],'width':v['Width'],'height':v['Height']}
def capture():
 import mss, mss.tools
 reg=region()
 with mss.mss() as s:
  mon=reg if reg else s.monitors[0]; shot=s.grab(mon); raw=mss.tools.to_png(shot.rgb,shot.size)
 import gi
 gi.require_version('GdkPixbuf','2.0')
 from gi.repository import GdkPixbuf
 loader=GdkPixbuf.PixbufLoader.new(); loader.write(raw); loader.close(); pix=loader.get_pixbuf(); edge=max(pix.get_width(),pix.get_height())
 if edge>1568:
  ratio=1568/edge; pix=pix.scale_simple(max(1,round(pix.get_width()*ratio)),max(1,round(pix.get_height()*ratio)),GdkPixbuf.InterpType.BILINEAR)
 with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as f: path=f.name
 try:
  if not pix.savev(path,'png',[],[]): raise RuntimeError('Could not encode resized screen capture as PNG.')
  data=Path(path).read_bytes()
 finally:
  try: os.unlink(path)
  except OSError: pass
 return base64.b64encode(data).decode('ascii'),'image/png'
def self_check():
 envload(); out=[]
 try:
  import gi,requests,mss
  gi.require_version('Gtk','3.0'); from gi.repository import Gtk
  out.append((1,'dependency imports','GTK3, requests, mss imported','Install/enable GTK3, requests, and mss in the venv.'))
 except Exception as e: out.append((0,'dependency imports',str(e),'Install/enable GTK3, requests, and mss in the venv.'))
 sess=os.getenv('XDG_SESSION_TYPE','').lower(); disp=os.getenv('DISPLAY','')
 try: xok=bool(disp) and sess!='wayland' and subprocess.run(['xset','-q'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3).returncode==0
 except (OSError,subprocess.TimeoutExpired): xok=False
 out.append((xok,'DISPLAY / X11',f'DISPLAY={disp or "unset"}; session={sess or "unspecified"}','Log into an Xfce X11 session; Wayland is unsupported.'))
 tools=all(shutil.which(x) for x in ('xdotool','xwininfo')); out.append((tools,'xdotool + xwininfo','both available' if tools else 'one or both missing','Install xdotool and x11-utils for window-scope capture.'))
 try: key_for(); good,detail=1,f'{cfg()["provider"]} API key configured'
 except Exception as e: good,detail=0,str(e)
 out.append((good,'provider API key',detail,'Set the matching API key in tools/sentinel/.env.'))
 try:
  dbinit()
  with sqlite3.connect(DB) as d: d.execute('SELECT 1').fetchone()
  out.append((1,'SQLite open',str(DB),'Check XDG_DATA_HOME permissions and free space.'))
 except Exception as e: out.append((0,'SQLite open',str(e),'Check XDG_DATA_HOME permissions and free space.'))
 try:
  dirs(); (LOGS/'sentinel.log').open('a').close(); out.append((1,'log writable',str(LOGS/'sentinel.log'),'Check log directory permissions and free space.'))
 except Exception as e: out.append((0,'log writable',str(e),'Check log directory permissions and free space.'))
 for ok,n,d,h in out: print(f'{"PASS" if ok else "FAIL"} | {n} | {d} | Fix: {h}')
 return 0 if all(x[0] for x in out) else 1
class Speech:
 def __init__(self): self.lock=threading.Lock(); self.proc=None; self.muted=False
 def stop(self):
  with self.lock: p=self.proc; self.proc=None
  if p and p.poll() is None:
   try: p.terminate()
   except OSError: pass
 def say(self,text):
  if self.muted or not text.strip(): return
  self.stop(); c=cfg(); exe=shutil.which('piper'); wav=None
  if c['tts']=='piper' and exe and c['voice']:
   try:
    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f: wav=f.name
    p=subprocess.Popen([exe,'--model',c['voice'],'--output_file',wav],stdin=subprocess.PIPE)
    with self.lock: self.proc=p
    p.communicate(text.encode(),timeout=90)
    if p.returncode==0 and shutil.which('aplay'):
     p=subprocess.Popen(['aplay','-q',wav]);
     with self.lock: self.proc=p
     p.wait(); return
   except (OSError,subprocess.TimeoutExpired): self.stop()
   finally:
    if wav:
     try: os.unlink(wav)
     except OSError: pass
  exe=shutil.which('espeak-ng')
  if exe:
   try:
    p=subprocess.Popen([exe,text]);
    with self.lock: self.proc=p
    p.wait()
   except OSError: pass
  with self.lock: self.proc=None
class Overlay:
 def __init__(self):
  import gi
  gi.require_version('Gtk','3.0'); from gi.repository import Gtk,Gdk,GLib
  self.Gtk,self.Gdk,self.GLib=Gtk,Gdk,GLib; self.w=Gtk.Window(title='Sentinel — screen answer'); self.w.set_default_size(460,190); self.w.set_keep_above(True); self.w.set_border_width(14)
  self.label=Gtk.Label(label='Capturing screen and asking Sentinel…'); self.label.set_line_wrap(True); self.label.set_selectable(True); self.w.add(self.label); self.w.connect('key-press-event',self.key); self.w.connect('delete-event',lambda *_:Gtk.main_quit()); self.w.show_all(); threading.Thread(target=self.work,daemon=True).start()
 def key(self,w,e):
  if e.keyval==self.Gdk.KEY_Escape: self.Gtk.main_quit(); return True
  return False
 def set(self,text): self.label.set_text(text); return False
 def work(self):
  try: im,mime=capture(); text=ask(DEFAULT_PROMPT,im,mime)
  except Exception as e: text=str(e)
  self.GLib.idle_add(self.set,text)
class App:
 GREETING='Hey Mel. Sentinel here. I can see your screen — ask me anything, or hit the mic.'
 def __init__(self):
  import gi
  gi.require_version('Gtk','3.0'); from gi.repository import Gtk,Gdk,GLib
  self.Gtk,self.Gdk,self.GLib=Gtk,Gdk,GLib; self.log=logger(); dbinit(); self.busy=False; self.voice=Speech()
  self.w=Gtk.Window(title='Sentinel'); self.w.set_default_size(420,640); self.w.set_size_request(360,460); self.w.connect('destroy',Gtk.main_quit); self.w.connect('key-press-event',self.key)
  box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=7); box.set_border_width(10); self.w.add(box)
  self.status=Gtk.Label(xalign=0); self.status.set_text(f'{cfg()["provider"]} / {cfg()["model"]}'); box.pack_start(self.status,False,False,0)
  self.scroll=Gtk.ScrolledWindow(); self.scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC); self.msgs=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); self.msgs.set_border_width(5); self.scroll.add(self.msgs); box.pack_start(self.scroll,True,True,0)
  bar=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=5); self.entry=Gtk.Entry(); self.entry.set_placeholder_text('Ask Sentinel about your screen…'); self.entry.connect('activate',lambda *_:self.send()); bar.pack_start(self.entry,True,True,0)
  for title,fn in [('Send',lambda *_:self.send()),('Mic',lambda *_:self.mic()),('Mute',lambda b:self.mute(b))]:
   b=Gtk.Button(label=title); b.connect('clicked',fn); bar.pack_start(b,False,False,0)
  box.pack_start(bar,False,False,0); self.detail=Gtk.Label(xalign=0); self.detail.set_text('Ready'); box.pack_start(self.detail,False,False,0)
  self.add('assistant',self.GREETING); self.w.show_all(); GLib.timeout_add_seconds(30,self.reminder_tick)
 def add(self,role,text):
  Gtk=self.Gtk; row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL); frame=Gtk.Frame(); frame.set_shadow_type(Gtk.ShadowType.IN); label=Gtk.Label(label=text); label.set_line_wrap(True); label.set_line_wrap_mode(2); label.set_max_width_chars(42); label.set_selectable(True); label.set_xalign(0); label.set_margin_start(9); label.set_margin_end(9); label.set_margin_top(6); label.set_margin_bottom(6); frame.add(label)
  if role=='user': row.pack_start(Gtk.Label(),True,True,0); row.pack_start(frame,False,False,0)
  else: row.pack_start(frame,False,False,0); row.pack_start(Gtk.Label(),True,True,0)
  self.msgs.pack_start(row,False,False,0); self.msgs.show_all(); self.GLib.idle_add(self.scroll_bottom); return label
 def scroll_bottom(self):
  a=self.scroll.get_vadjustment(); a.set_value(a.get_upper()); return False
 def send(self):
  text=self.entry.get_text().strip()
  if not text or self.busy: return
  self.entry.set_text(''); self.busy=True; self.detail.set_text('Capturing screen…'); self.add('user',text); reply=self.add('assistant','Thinking…'); threading.Thread(target=self.ask_worker,args=(text,reply),daemon=True).start()
 def ask_worker(self,text,label):
  try:
   im,mime=capture(); answer=ask(text,im,mime); self.log.info(json.dumps({'event':'response','provider':cfg()['provider']})); prune(); self.GLib.idle_add(self.finish,label,answer,False)
   threading.Thread(target=self.voice.say,args=(answer,),daemon=True).start()
  except Exception as e:
   self.log.exception('request_error'); self.GLib.idle_add(self.finish,label,str(e),True)
 def finish(self,label,text,error):
  label.set_text(text); self.busy=False; self.detail.set_text('Error' if error else f'{cfg()["provider"]} / {cfg()["model"]}'); self.scroll_bottom(); return False
 def mute(self,b):
  self.voice.muted=not self.voice.muted
  if self.voice.muted: self.voice.stop(); b.set_label('Unmute')
  else: b.set_label('Mute')
 def mic(self):
  if self.busy: return
  self.busy=True; self.detail.set_text('Recording for up to 8 seconds…'); threading.Thread(target=self.record,daemon=True).start()
 def record(self):
  path=None
  try:
   with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f: path=f.name
   p=subprocess.run(['arecord','-q','-f','S16_LE','-r','16000','-c','1','-d','8',path],capture_output=True,text=True,timeout=12)
   if p.returncode: raise RuntimeError(p.stderr.strip() or f'arecord failed ({p.returncode})')
   audio=base64.b64encode(Path(path).read_bytes()).decode('ascii'); text=transcribe(audio).strip()
   if not text: raise RuntimeError('Gemini returned an empty transcription.')
   self.GLib.idle_add(self.transcribed,text)
  except Exception as e: self.GLib.idle_add(self.mic_error,str(e))
  finally:
   if path:
    try: os.unlink(path)
    except OSError: pass
 def transcribed(self,text): self.entry.set_text(text); self.busy=False; self.send(); return False
 def mic_error(self,text): self.busy=False; self.detail.set_text('Error'); self.add('assistant',text); return False
 def key(self,w,e):
  if e.keyval==self.Gdk.KEY_Escape: self.w.destroy(); return True
  if e.state & self.Gdk.ModifierType.CONTROL_MASK and e.keyval==self.Gdk.KEY_r: self.reminder_dialog(); return True
  return False
 def reminder_dialog(self):
  d=self.Gtk.Dialog(title='Add reminder',transient_for=self.w,flags=self.Gtk.DialogFlags.MODAL); d.add_button('Cancel',self.Gtk.ResponseType.CANCEL); d.add_button('Save',self.Gtk.ResponseType.OK); e=self.Gtk.Entry(); e.set_placeholder_text('e.g. Call Sam tomorrow at 9am'); d.get_content_area().pack_start(e,True,True,10); e.show(); ok=d.run()==self.Gtk.ResponseType.OK; text=e.get_text().strip(); d.destroy()
  if ok and text: threading.Thread(target=self.save_reminder,args=(text,),daemon=True).start()
 def save_reminder(self,text):
  try:
   now=dt.datetime.now().astimezone().isoformat(); result=gemini(f'Interpret this reminder relative to {now}. Return ONLY JSON: {{"title":"short reminder","due_at":"ISO-8601 datetime including timezone"}}. Reminder: {text}')
   data=json.loads(result); due=dt.datetime.fromisoformat(data['due_at'].replace('Z','+00:00'))
   if due.tzinfo is None: due=due.astimezone()
   title=str(data['title']).strip()
   if not title: raise ValueError('Reminder title is empty')
   with sqlite3.connect(DB) as db: db.execute('INSERT INTO reminders(title,due_at,created_at) VALUES(?,?,?)',(title,due.isoformat(),dt.datetime.now().astimezone().isoformat()))
   msg=f'Saved reminder: {title} — {due.astimezone().strftime("%Y-%m-%d %H:%M %Z")}'
  except Exception as e: msg='Could not save reminder: '+str(e)
  self.GLib.idle_add(self.add,'assistant',msg)
 def reminder_tick(self):
  try:
   now=dt.datetime.now().astimezone()
   with sqlite3.connect(DB) as db:
    for ident,title,due in db.execute('SELECT id,title,due_at FROM reminders WHERE notified=0').fetchall():
     when=dt.datetime.fromisoformat(due)
     if when.tzinfo is None: when=when.astimezone()
     if when<=now:
      subprocess.run(['notify-send','Sentinel reminder',title],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5); db.execute('UPDATE reminders SET notified=1 WHERE id=?',(ident,)); self.log.info('reminder_due id=%s title=%s',ident,title)
  except Exception as e: self.log.exception('reminder_error: %s',e)
  return True
def main():
 p=argparse.ArgumentParser(); p.add_argument('--self-check',action='store_true'); p.add_argument('--capture',action='store_true'); a=p.parse_args()
 if a.self_check: return self_check()
 import gi
 gi.require_version('Gtk','3.0'); from gi.repository import Gtk
 if a.capture: Overlay()
 else: App()
 Gtk.main(); return 0
if __name__=='__main__': sys.exit(main())
