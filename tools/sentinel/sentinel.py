#!/usr/bin/env python3
"""Sentinel GTK3/X11 assistant. Hotkeys are installed externally; --capture and --plan are IPC modes."""
import base64, datetime as dt, json, logging, logging.handlers, os, re, shlex, shutil, socket, sqlite3, subprocess, sys, threading, time, traceback
from pathlib import Path
import requests
import gi
gi.require_version('Gtk','3.0'); gi.require_version('Gdk','3.0'); gi.require_version('GdkPixbuf','2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

PROVIDERS={'anthropic':('claude-sonnet-4-5-20250929','ANTHROPIC_API_KEY'),'openai':('gpt-4o-mini','OPENAI_API_KEY'),'gemini':('gemini-2.5-flash','GEMINI_API_KEY')}
MAX_STORAGE=500*1024*1024; IDLE_LIMIT=300000

def load_env(path):
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            s=line.strip()
            if s and not s.startswith('#') and '=' in s:
                k,v=s.split('=',1); v=v.strip()
                if len(v)>1 and v[0] in "\"'" and v[-1]==v[0]: v=v[1:-1]
                if k.strip() not in os.environ: os.environ[k.strip()]=v
    except OSError: pass

class Sentinel:
    def __init__(self):
        here=Path(__file__).resolve().parent
        self.data=Path(os.getenv('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'sentinel'
        self.conf=Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'sentinel'
        self.data.mkdir(parents=True,exist_ok=True); self.conf.mkdir(parents=True,exist_ok=True)
        self.shots=self.data/'screenshots'; self.shots.mkdir(exist_ok=True)
        for p in (here/'.env',here.parent.parent/'.env',self.conf/'.env'): load_env(p)
        self.logfile=self.data/'sentinel.log'; self.dbfile=self.data/'reminders.sqlite3'
        self.sockpath=Path(os.getenv('XDG_RUNTIME_DIR','/tmp'))/('sentinel-%s.sock'%os.getuid())
        self.allowfile=self.conf/'safety.allowlist'; self.settingsfile=self.conf/'settings.json'
        self.logger=logging.getLogger('sentinel'); self.logger.setLevel(logging.INFO); self.logger.propagate=False
        h=logging.handlers.RotatingFileHandler(self.logfile,maxBytes=8*1024*1024,backupCount=4,encoding='utf8')
        h.setFormatter(logging.Formatter('%(message)s')); self.logger.addHandler(h)
        self.settings=self.read_settings(); self.paused=False; self.overlay=None; self.steps=[]; self.server=None
        self.dbinit(); self.prune(); self.start_ipc(); self.tray_init()
        GLib.timeout_add_seconds(30,self.reminder_tick); GLib.timeout_add_seconds(60,self.prune)
        self.log('daemon_started',{'pid':os.getpid()})

    def read_settings(self):
        s={'provider':'anthropic','model':'','keep_screenshots':False}
        try:
            d=json.loads(self.settingsfile.read_text()); s.update({k:d[k] for k in s if k in d})
        except (OSError,ValueError,TypeError): pass
        p=os.getenv('SENTINEL_PROVIDER',s['provider']).lower().strip(); s['provider']=p if p in PROVIDERS else 'anthropic'
        s['model']=os.getenv('SENTINEL_MODEL',s.get('model') or '').strip()
        if 'SENTINEL_KEEP_SCREENSHOTS' in os.environ: s['keep_screenshots']=os.getenv('SENTINEL_KEEP_SCREENSHOTS','').lower() in ('1','true','yes','on')
        return s
    def save_settings(self):
        try: self.settingsfile.write_text(json.dumps(self.settings,indent=2)+'\n'); os.chmod(self.settingsfile,0o600); self.log('settings_saved',{'provider':self.settings['provider']})
        except OSError as e: self.log('settings_error',{'error':str(e)})
    def log(self,event,data=None):
        try: self.logger.info(json.dumps({'timestamp':dt.datetime.now().astimezone().isoformat(timespec='seconds'),'event':event,'data':data or {}},ensure_ascii=False,default=str)); self.prune()
        except Exception: pass
    def prune(self):
        try:
            files=[]
            for root,_,names in os.walk(self.data):
                for n in names:
                    p=Path(root)/n
                    try: files.append((p.stat().st_mtime,p,p.stat().st_size))
                    except OSError: pass
            total=sum(x[2] for x in files)
            for _,p,size in sorted(files):
                if total<=MAX_STORAGE: break
                if p in (self.logfile,self.dbfile): continue
                try: p.unlink(); total-=size
                except OSError: pass
        except Exception: pass
        return GLib.SOURCE_CONTINUE
    def dbinit(self):
        try:
            with sqlite3.connect(self.dbfile) as db: db.execute('CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY,title TEXT NOT NULL,due_at TEXT NOT NULL,created_at TEXT NOT NULL,notified INTEGER NOT NULL DEFAULT 0)')
            os.chmod(self.dbfile,0o600)
        except Exception as e: self.log('reminder_db_error',{'error':str(e)})
    def start_ipc(self):
        self.sockpath.parent.mkdir(parents=True,exist_ok=True)
        if self.sockpath.exists():
            probe=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            try: probe.settimeout(.2); probe.connect(str(self.sockpath)); raise RuntimeError('Sentinel is already running')
            except (ConnectionRefusedError,FileNotFoundError,socket.timeout):
                try: self.sockpath.unlink()
                except OSError: pass
            finally: probe.close()
        self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); self.server.bind(str(self.sockpath)); os.chmod(self.sockpath,0o600); self.server.listen(8); self.server.setblocking(False)
        GLib.io_add_watch(self.server,GLib.IO_IN|GLib.IO_ERR|GLib.IO_HUP,self.ipc_ready)
    def ipc_ready(self,src,cond):
        if cond&(GLib.IO_ERR|GLib.IO_HUP): return GLib.SOURCE_CONTINUE
        try:
            c,_=src.accept(); c.settimeout(.4); raw=b''
            while len(raw)<8192 and b'\n' not in raw:
                b=c.recv(1024)
                if not b: break
                raw+=b
            try: req=json.loads(raw.split(b'\n',1)[0].decode())
            except (ValueError,UnicodeDecodeError): req={}
            c.sendall(b'OK\n'); c.close()
            if isinstance(req,dict): GLib.idle_add(self.dispatch,req)
        except (OSError,BlockingIOError) as e: self.log('ipc_error',{'error':str(e)})
        return GLib.SOURCE_CONTINUE
    def dispatch(self,r):
        a=str(r.get('action','')).lower()
        if a in ('capture','plan'): self.begin(a,str(r.get('prompt','')).strip())
        elif a=='settings': self.show_settings()
        elif a=='logs': self.show_logs()
        elif a=='pause': self.paused=not self.paused; self.log('paused',{'paused':self.paused})
        elif a=='quit': self.log('daemon_stopping'); Gtk.main_quit()
        elif a=='remind': self.add_reminder(str(r.get('text','')).strip())
        return GLib.SOURCE_REMOVE
    def tray_init(self):
        try:
            self.tray=Gtk.StatusIcon.new_from_icon_name('preferences-desktop-notification'); self.tray.set_visible(True); self.tray.set_tooltip_text('Sentinel screen assistant'); self.tray.connect('popup-menu',self.tray_menu); self.tray.connect('activate',lambda *_:self.begin('capture',''))
        except Exception as e: self.log('tray_unavailable',{'error':str(e)})
    def tray_menu(self,icon,button,when):
        menu=Gtk.Menu()
        opts=[('Capture / Ask',lambda:self.begin('capture','')),('Create action plan',lambda:self.begin('plan','')),('Add reminder…',self.reminder_dialog),('Settings…',self.show_settings),('View log…',self.show_logs),(('Resume' if self.paused else 'Pause')+' processing',self.toggle_pause),('Quit',lambda:self.dispatch({'action':'quit'}))]
        for label,cb in opts:
            item=Gtk.MenuItem(label=label); item.connect('activate',lambda _,f=cb:f()); menu.append(item)
        menu.show_all(); menu.popup(None,None,Gtk.StatusIcon.position_menu,icon,button,when)
    def toggle_pause(self): self.paused=not self.paused; self.log('paused',{'paused':self.paused})
    def screen_guard(self):
        try:
            q=subprocess.run(['xset','q'],capture_output=True,text=True,timeout=2)
            m=re.search(r'Monitor is\s+(Off|On)',q.stdout,re.I)
            if m and m.group(1).lower()=='off': return 'Monitor is off (DPMS)'
        except (OSError,subprocess.TimeoutExpired): pass
        try:
            q=subprocess.run(['xprintidle'],capture_output=True,text=True,timeout=2)
            if q.returncode==0 and q.stdout.strip().isdigit() and int(q.stdout.strip())>IDLE_LIMIT: return 'User idle for more than five minutes'
        except (OSError,subprocess.TimeoutExpired): pass
        return None
    def screenshot(self):
        try:
            import mss
            with mss.mss() as s:
                shot=s.grab(s.monitors[0]); w,h=shot.size; raw=shot.rgb
            pix=GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(raw),GdkPixbuf.Colorspace.RGB,False,8,w,h,w*3)
        except ImportError:
            root=Gdk.get_default_root_window()
            if root is None: raise RuntimeError('No X11 root window available')
            pix=Gdk.pixbuf_get_from_window(root,0,0,root.get_width(),root.get_height())
            if pix is None: raise RuntimeError('Could not capture X11 desktop')
        if pix.get_width()>1568: pix=pix.scale_simple(1568,max(1,int(pix.get_height()*1568/pix.get_width())),GdkPixbuf.InterpType.BILINEAR)
        saved=pix.save_to_bufferv('png',[],[])
        if isinstance(saved,tuple):
            if len(saved)==2 and isinstance(saved[0],bool):
                if not saved[0]: raise RuntimeError('Could not encode screenshot')
                saved=saved[1]
            else: saved=saved[-1]
        return (saved.encode('latin1') if isinstance(saved,str) else bytes(saved)),pix.get_width(),pix.get_height()
    def begin(self,mode,prompt=''):
        if self.paused: self.message('Sentinel is paused. Resume from the tray menu.'); self.log('capture_skipped',{'reason':'paused'}); return
        why=self.screen_guard()
        if why: self.message('Skipped: '+why); self.log('capture_skipped',{'reason':why}); return
        try: image,w,h=self.screenshot()
        except Exception as e: self.log('capture_error',{'error':str(e),'trace':traceback.format_exc()}); self.message('Screen capture failed. See Sentinel log.'); return
        stamp=dt.datetime.now().astimezone().strftime('%Y%m%d-%H%M%S-%f'); file=self.shots/(stamp+'.png')
        try: file.write_bytes(image); os.chmod(file,0o600)
        except OSError: file=None
        prompt=prompt or ('Create a cautious step-by-step action plan for the request.' if mode=='plan' else 'Describe what is visible and help with the request.')
        self.log('capture',{'mode':mode,'width':w,'height':h,'screenshot':str(file) if file else None,'prompt':prompt})
        self.show_overlay(mode,prompt); self.overlay.status.set_text('Capturing and contacting '+self.settings['provider']+'…'); self.overlay.spinner.start()
        threading.Thread(target=self.request_worker,args=(mode,prompt,image,file),daemon=True).start()
    def show_overlay(self,mode,prompt):
        if self.overlay:
            try:self.overlay.destroy()
            except Exception:pass
        self.overlay=Overlay(self,mode,prompt); self.overlay.show_all(); self.overlay.spinner.start()
        try:
            d=Gdk.Display.get_default(); seat=d.get_default_seat(); pointer=seat.get_pointer(); screen,x,y=pointer.get_position(); m=screen.get_monitor_at_point(x,y); r=screen.get_monitor_geometry(m)
            self.overlay.move(min(max(r.x,x+18),r.x+r.width-520),min(max(r.y,y+18),r.y+r.height-380))
        except Exception:pass
        self.overlay.set_keep_above(True); self.overlay.present()
    def message(self,text):
        if not self.overlay: self.overlay=Overlay(self,'capture','')
        self.overlay.show_all(); self.overlay.spinner.stop(); self.overlay.status.set_text(text); self.overlay.answer.set_text(text); self.overlay.set_keep_above(True); self.overlay.present()
    def model_name(self): return self.settings.get('model') or PROVIDERS[self.settings['provider']][0]
    def request_worker(self,mode,prompt,image,file):
        try:
            self.log('request',{'mode':mode,'provider':self.settings['provider'],'model':self.model_name(),'prompt':prompt})
            result=self.call_model(mode,prompt,image)
            self.log('response',{'mode':mode,'provider':self.settings['provider'],'model':self.model_name(),'response':result})
            GLib.idle_add(self.request_done,mode,result)
        except Exception as e: self.log('request_error',{'error':str(e),'trace':traceback.format_exc()}); GLib.idle_add(self.request_failed,str(e))
        finally:
            if file and not self.settings.get('keep_screenshots',False):
                try:file.unlink(missing_ok=True)
                except OSError:pass
            self.prune()
    @staticmethod
    def parse_json(text):
        text=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip(),flags=re.I)
        try:return json.loads(text)
        except ValueError:
            m=re.search(r'\{.*\}',text,re.S)
            if not m:raise ValueError('Model did not return valid JSON')
            return json.loads(m.group())
    def call_model(self,mode,prompt,png):
        provider=self.settings['provider']; model=self.model_name(); key=os.getenv(PROVIDERS[provider][1],'').strip()
        if not key:raise RuntimeError('Missing '+PROVIDERS[provider][1]+' in environment or .env')
        img=base64.b64encode(png).decode('ascii'); user=prompt
        if mode=='plan':user+='\nReturn JSON only: {"steps":[{"type":"shell","command":"...","description":"..."}]}. Only shell, keystroke, click types.'
        system='You are Sentinel, a careful desktop assistant. Do not claim to have acted. Action plans must be JSON steps with type shell/keystroke/click; shell has command, keystroke has keys, click has numeric x,y. Explain risks and keep actions minimal.'
        if provider=='anthropic':
            r=requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':key,'anthropic-version':'2023-06-01'},json={'model':model,'max_tokens':1800,'system':system,'messages':[{'role':'user','content':[{'type':'image','source':{'type':'base64','media_type':'image/png','data':img}},{'type':'text','text':user}]}]},timeout=(10,120)); r.raise_for_status(); text=''.join(x.get('text','') for x in r.json().get('content',[]) if x.get('type')=='text')
        elif provider=='openai':
            r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':model,'max_tokens':1800,'messages':[{'role':'system','content':system},{'role':'user','content':[{'type':'text','text':user},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+img}}]}]},timeout=(10,120)); r.raise_for_status(); text=r.json()['choices'][0]['message']['content']
        else:
            r=requests.post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',headers={'x-goog-api-key':key},json={'systemInstruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':[{'text':user},{'inline_data':{'mime_type':'image/png','data':img}}]}],'generationConfig':{'maxOutputTokens':1800}},timeout=(10,120)); r.raise_for_status(); text=''.join(p.get('text','') for p in r.json().get('candidates',[{}])[0].get('content',{}).get('parts',[]))
        if mode!='plan':return str(text).strip()
        obj=self.parse_json(str(text))
        if not isinstance(obj,dict) or not isinstance(obj.get('steps'),list):raise ValueError('Plan JSON must contain steps array')
        out=[]
        for s in obj['steps'][:30]:
            if not isinstance(s,dict) or s.get('type') not in ('shell','keystroke','click'):continue
            t=s['type']; v={'type':t,'description':str(s.get('description',''))[:500]}
            if t=='shell' and isinstance(s.get('command'),str):v['command']=s['command'][:4000]
            elif t=='keystroke' and isinstance(s.get('keys'),str):v['keys']=s['keys'][:200]
            elif t=='click' and isinstance(s.get('x'),(int,float)) and isinstance(s.get('y'),(int,float)):v.update(x=int(s['x']),y=int(s['y']),button=int(s.get('button',1)) if str(s.get('button',1)).isdigit() else 1)
            else:continue
            out.append(v)
        return {'steps':out}
    def request_done(self,mode,result):
        if not self.overlay:return GLib.SOURCE_REMOVE
        self.overlay.spinner.stop(); self.overlay.status.set_text('Action plan ready — review before proceeding.' if mode=='plan' else 'Response ready')
        if mode=='plan':self.steps=result.get('steps',[]); self.overlay.show_plan(self.steps)
        else:self.overlay.show_answer(str(result))
        return GLib.SOURCE_REMOVE
    def request_failed(self,error):
        if self.overlay:self.overlay.spinner.stop(); self.overlay.status.set_text('Request failed — see log for details'); self.overlay.show_answer(error)
        return GLib.SOURCE_REMOVE
    def allowed_commands(self):
        try:return {line.strip() for line in self.allowfile.read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')}
        except OSError:return set()
    def destructive(self,command):return bool(re.search(r'(^|[;&|\s])(sudo|rm|rmdir|mkfs|dd|shutdown|reboot|poweroff|kill|chmod|chown|wipefs)(\s|$)',command,re.I))
    def confirm_plan(self,steps):
        if not steps:self.message('The model returned no valid action steps.'); return
        d=Gtk.MessageDialog(transient_for=self.overlay,flags=Gtk.DialogFlags.MODAL,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.NONE,text='Run this action plan?')
        d.format_secondary_text('Actions will run only after confirmation. Shell commands must exactly match a line in '+str(self.allowfile)+'.'); d.add_button('Cancel',Gtk.ResponseType.CANCEL); d.add_button('Confirm plan',Gtk.ResponseType.ACCEPT)
        ok=d.run()==Gtk.ResponseType.ACCEPT; d.destroy()
        if not ok:return
        allowed=self.allowed_commands(); todo=[]
        for s in steps:
            if s['type']=='shell':
                cmd=s['command']
                if cmd not in allowed:self.log('action_blocked',{'reason':'not in safety.allowlist','command':cmd}); continue
                if self.destructive(cmd):
                    d=Gtk.MessageDialog(transient_for=self.overlay,flags=Gtk.DialogFlags.MODAL,message_type=Gtk.MessageType.WARNING,buttons=Gtk.ButtonsType.NONE,text='Destructive command — confirm again')
                    d.format_secondary_text(cmd); d.add_button('Cancel command',Gtk.ResponseType.CANCEL); d.add_button('Run command',Gtk.ResponseType.ACCEPT)
                    ok=d.run()==Gtk.ResponseType.ACCEPT; d.destroy()
                    if not ok:self.log('action_cancelled',{'command':cmd}); continue
            todo.append(s)
        self.log('action_confirmed',{'steps':todo})
        self.overlay.status.set_text('Running confirmed steps…')
        threading.Thread(target=self.run_steps,args=(todo,),daemon=True).start()
    def run_steps(self,steps):
        outcomes=[]
        for s in steps:
            try:
                if s['type']=='shell':
                    p=subprocess.run(['/bin/bash','-lc',s['command']],capture_output=True,text=True,timeout=60); result={'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-2000:]}
                elif s['type']=='keystroke':
                    if not shutil.which('xdotool'):raise RuntimeError('xdotool is required for keystroke actions')
                    p=subprocess.run(['xdotool','key',s['keys']],capture_output=True,text=True,timeout=10); result={'returncode':p.returncode}
                else:
                    if not shutil.which('xdotool'):raise RuntimeError('xdotool is required for click actions')
                    p=subprocess.run(['xdotool','mousemove','--sync',str(s['x']),str(s['y']),'click',str(s.get('button',1))],capture_output=True,text=True,timeout=10); result={'returncode':p.returncode}
                outcomes.append({'step':s,'result':result}); self.log('action',outcomes[-1])
            except Exception as e:outcomes.append({'step':s,'error':str(e)}); self.log('action_error',outcomes[-1])
        GLib.idle_add(self.steps_done,outcomes)
    def steps_done(self,results):
        if self.overlay:self.overlay.status.set_text('Action plan finished.'); self.overlay.show_answer(json.dumps(results,indent=2,ensure_ascii=False))
        return GLib.SOURCE_REMOVE
    def show_settings(self):
        d=Gtk.Dialog(title='Sentinel settings',transient_for=self.overlay,flags=Gtk.DialogFlags.MODAL); d.add_button('Cancel',Gtk.ResponseType.CANCEL); d.add_button('Save',Gtk.ResponseType.OK)
        box=d.get_content_area(); grid=Gtk.Grid(column_spacing=10,row_spacing=10,margin=12); box.add(grid)
        provider=Gtk.ComboBoxText(); [provider.append_text(p) for p in PROVIDERS]; provider.set_active(list(PROVIDERS).index(self.settings['provider']))
        model=Gtk.Entry(); model.set_text(self.settings.get('model','')); model.set_placeholder_text('Leave blank for provider default')
        keep=Gtk.CheckButton(label='Keep screenshots after processing'); keep.set_active(bool(self.settings['keep_screenshots']))
        grid.attach(Gtk.Label(label='Provider'),0,0,1,1); grid.attach(provider,1,0,1,1); grid.attach(Gtk.Label(label='Model override'),0,1,1,1); grid.attach(model,1,1,1,1); grid.attach(keep,0,2,2,1)
        tip=Gtk.Label(label='API keys are read from .env/environment. Shell action allowlist: '+str(self.allowfile)); tip.set_line_wrap(True); grid.attach(tip,0,3,2,1)
        d.show_all()
        if d.run()==Gtk.ResponseType.OK:
            self.settings.update(provider=provider.get_active_text().lower(),model=model.get_text().strip(),keep_screenshots=keep.get_active()); self.save_settings()
        d.destroy()
    def show_logs(self):
        w=Gtk.Window(title='Sentinel log'); w.set_default_size(760,520); box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6); w.add(box)
        view=Gtk.TextView(); view.set_editable(False); view.set_cursor_visible(False); view.get_buffer().set_text(self.logfile.read_text(errors='replace')[-100000:] if self.logfile.exists() else 'No log entries yet.')
        scroll=Gtk.ScrolledWindow(); scroll.add(view); box.pack_start(scroll,True,True,0); w.show_all()
    def reminder_dialog(self):
        d=Gtk.Dialog(title='Add reminder',transient_for=self.overlay,flags=Gtk.DialogFlags.MODAL); d.add_button('Cancel',Gtk.ResponseType.CANCEL); d.add_button('Parse and save',Gtk.ResponseType.OK)
        box=d.get_content_area(); e=Gtk.Entry(); e.set_placeholder_text('e.g. remind me to call Sam tomorrow at 9am'); box.add(e); box.show_all()
        if d.run()==Gtk.ResponseType.OK:self.add_reminder(e.get_text().strip())
        d.destroy()
    def add_reminder(self,text):
        if not text:return
        self.message('Parsing reminder time…')
        threading.Thread(target=self.reminder_worker,args=(text,),daemon=True).start()
    def reminder_worker(self,text):
        try:
            provider=self.settings['provider']; model=self.model_name(); key=os.getenv(PROVIDERS[provider][1],'').strip()
            if not key:raise RuntimeError('Missing API key for reminder parsing')
            now=dt.datetime.now().astimezone().isoformat(timespec='seconds')
            prompt='Parse this reminder relative to local current time '+now+'. Return JSON only {"title":"...","due_at":"ISO-8601 with timezone"}. Reminder: '+text
            if provider=='anthropic':
                r=requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':key,'anthropic-version':'2023-06-01'},json={'model':model,'max_tokens':300,'messages':[{'role':'user','content':prompt}]},timeout=(10,60)); r.raise_for_status(); out=''.join(x.get('text','') for x in r.json().get('content',[]))
            elif provider=='openai':
                r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':model,'max_tokens':300,'messages':[{'role':'user','content':prompt}]},timeout=(10,60)); r.raise_for_status(); out=r.json()['choices'][0]['message']['content']
            else:
                r=requests.post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',headers={'x-goog-api-key':key},json={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'maxOutputTokens':300}},timeout=(10,60)); r.raise_for_status(); out=r.json()['candidates'][0]['content']['parts'][0]['text']
            obj=self.parse_json(out); title=str(obj['title']).strip(); due=dt.datetime.fromisoformat(str(obj['due_at']).replace('Z','+00:00'))
            if due.tzinfo is None:due=due.astimezone()
            with sqlite3.connect(self.dbfile) as db: db.execute('INSERT INTO reminders(title,due_at,created_at) VALUES(?,?,?)',(title,due.isoformat(),dt.datetime.now().astimezone().isoformat()))
            self.log('reminder_created',{'title':title,'due_at':due.isoformat()}); GLib.idle_add(self.reminder_done,'Reminder saved: '+title+' — '+due.astimezone().strftime('%Y-%m-%d %H:%M'))
        except Exception as e:self.log('reminder_error',{'error':str(e)}); GLib.idle_add(self.reminder_done,'Could not add reminder. See Sentinel log.')
    def reminder_done(self,msg):
        if self.overlay:self.overlay.status.set_text(msg)
        return GLib.SOURCE_REMOVE
    def reminder_tick(self):
        try:
            now=dt.datetime.now().astimezone()
            with sqlite3.connect(self.dbfile) as db:
                rows=db.execute('SELECT id,title,due_at FROM reminders WHERE notified=0').fetchall()
                for ident,title,due_s in rows:
                    due=dt.datetime.fromisoformat(due_s)
                    if due.tzinfo is None:due=due.astimezone()
                    if due<=now:
                        try:subprocess.run(['notify-send','Sentinel reminder',title],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
                        except (OSError,subprocess.TimeoutExpired):pass
                        db.execute('UPDATE reminders SET notified=1 WHERE id=?',(ident,)); self.log('reminder_due',{'id':ident,'title':title,'due_at':due_s})
        except Exception as e:self.log('reminder_error',{'error':str(e)})
        return GLib.SOURCE_CONTINUE

class Overlay(Gtk.Window):
    def __init__(self,app,mode,prompt):
        super().__init__(type=Gtk.WindowType.TOPLEVEL); self.app=app; self.mode=mode; self.set_title('Sentinel'); self.set_default_size(500,380); self.set_resizable(True); self.set_keep_above(True); self.set_border_width(10)
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); self.add(outer)
        bar=Gtk.Box(spacing=8); self.spinner=Gtk.Spinner(); bar.pack_start(self.spinner,False,False,0); self.status=Gtk.Label(label='Ready'); self.status.set_xalign(0); bar.pack_start(self.status,True,True,0)
        close=Gtk.Button(label='Close'); close.connect('clicked',lambda *_:self.destroy()); bar.pack_end(close,False,False,0); outer.pack_start(bar,False,False,0)
        self.entry=Gtk.Entry(); self.entry.set_placeholder_text('Ask about this screen…'); self.entry.set_text(prompt if mode=='plan' and prompt else ''); outer.pack_start(self.entry,False,False,0)
        ask=Gtk.Box(spacing=6); go=Gtk.Button(label='Ask'); plan=Gtk.Button(label='Plan actions'); go.connect('clicked',lambda *_:self.app.begin('capture',self.entry.get_text().strip())); plan.connect('clicked',lambda *_:self.app.begin('plan',self.entry.get_text().strip())); ask.pack_start(go,False,False,0); ask.pack_start(plan,False,False,0); outer.pack_start(ask,False,False,0)
        self.answer=Gtk.Label(label=''); self.answer.set_xalign(0); self.answer.set_yalign(0); self.answer.set_line_wrap(True); self.answer.set_selectable(True)
        self.planbox=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5); outer.pack_start(self.planbox,False,False,0)
        scroll=Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC); scroll.add(self.answer); outer.pack_start(scroll,True,True,0)
        self.connect('key-press-event',self.keypress); self.connect('destroy',self.closed)
    def keypress(self,_,event):
        if event.keyval==Gdk.KEY_Escape:self.destroy(); return True
        return False
    def closed(self,*_):
        if self.app.overlay is self:self.app.overlay=None
    def show_answer(self,text):
        self.planbox.hide(); self.answer.set_text(text); self.answer.show()
    def show_plan(self,steps):
        self.planbox.show_all(); self.answer.set_text(''); self.answer.show()
        for child in self.planbox.get_children():self.planbox.remove(child)
        for i,s in enumerate(steps,1):
            detail=s.get('description') or (s.get('command') or s.get('keys') or ('click x=%s y=%s'%(s.get('x'),s.get('y'))))
            row=Gtk.Label(label='%d. [%s] %s'%(i,s['type'],detail)); row.set_xalign(0); row.set_line_wrap(True); self.planbox.pack_start(row,False,False,0)
        run=Gtk.Button(label='Confirm and run plan'); cancel=Gtk.Button(label='Dismiss plan'); controls=Gtk.Box(spacing=6); controls.pack_start(run,False,False,0); controls.pack_start(cancel,False,False,0)
        run.connect('clicked',lambda *_:self.app.confirm_plan(steps)); cancel.connect('clicked',lambda *_:self.app.log('action_plan_dismissed'))
        self.planbox.pack_start(controls,False,False,0); self.planbox.show_all()

def send_ipc(action,**values):
    path=Path(os.getenv('XDG_RUNTIME_DIR','/tmp'))/('sentinel-%s.sock'%os.getuid()); payload=json.dumps({'action':action,**values}).encode()+b'\n'
    c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); c.settimeout(1.5); c.connect(str(path)); c.sendall(payload); c.recv(32); c.close()
def main():
    import argparse
    p=argparse.ArgumentParser(description='Sentinel GTK3 screen assistant')
    p.add_argument('--capture',action='store_true',help='capture and ask'); p.add_argument('--plan',action='store_true',help='capture and request action plan'); p.add_argument('--settings',action='store_true'); p.add_argument('--logs',action='store_true'); p.add_argument('--pause',action='store_true'); p.add_argument('--quit',action='store_true'); p.add_argument('--remind',metavar='TEXT'); p.add_argument('--daemon',action='store_true',help='run foreground GTK daemon'); a=p.parse_args()
    action='plan' if a.plan else 'capture' if a.capture else 'settings' if a.settings else 'logs' if a.logs else 'pause' if a.pause else 'quit' if a.quit else 'remind' if a.remind is not None else None
    if action:
        payload={'text':a.remind} if action=='remind' else {}
        try:send_ipc(action,**payload); return 0
        except OSError:
            try:subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--daemon'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            except OSError:return 1
            for _ in range(40):
                time.sleep(.1)
                try:send_ipc(action,**payload); return 0
                except OSError:continue
            return 1
    try:
        app=Sentinel(); signal.signal(signal.SIGTERM,lambda *_:Gtk.main_quit()); Gtk.main()
    except Exception as e:
        try:print('Sentinel failed: '+str(e),file=sys.stderr)
        except Exception:pass
        return 1
    finally:
        try:
            path=Path(os.getenv('XDG_RUNTIME_DIR','/tmp'))/('sentinel-%s.sock'%os.getuid()); path.unlink(missing_ok=True)
        except OSError:pass
    return 0
if __name__=='__main__':raise SystemExit(main())