#!/usr/bin/env python3
"""KYLA online bridge — interactive brain for Pages/phone. Stdlib only. Port 8787."""
from __future__ import annotations
import json, os, subprocess, sys, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("KYLA_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("KYLA_BRIDGE_PORT", "8787"))
DEFAULT_AGENT = os.environ.get("KYLA_DEFAULT_AGENT", "ruflo")
TIMEOUT = int(os.environ.get("KYLA_BRIDGE_TIMEOUT", "180"))
STARTED = time.time()
ALLOWED = {"ruflo","ruflow","swarm","hive","stack","agent-reach","agent_reach","ollama","shell","clip","echo"}

# Optional Supabase sink (default-on, no-op without SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY).
sys.path.insert(0, str(ROOT / "tools"))
try:
    import supabase_sink as _sb
except Exception:  # noqa: BLE001 — never let persistence break the bridge
    _sb = None

def _sb_on():
    try: return bool(_sb and _sb.configured())
    except Exception: return False

def _sb_log(result, prompt, started_iso):
    """Fire-and-forget agent_runs row (source=bridge). Skipped when the web client already logged it."""
    if not _sb_on(): return
    try:
        _sb.log_run_async(agent=result.get("agent") or DEFAULT_AGENT, room=result.get("room"),
                          status="ok" if result.get("ok") else "error", input=prompt, output=result.get("reply"),
                          source="bridge", started_at=started_iso,
                          meta={"ms": result.get("ms"), "exit_code": result.get("exit_code")})
    except Exception: pass

def _cors(h):
    o = h.headers.get("Origin", "*") or "*"
    allow = o if (o.endswith(".github.io") or o.startswith("http://localhost") or o.startswith("http://127.0.0.1") or o=="null") else "*"
    h.send_header("Access-Control-Allow-Origin", allow)
    h.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    h.send_header("Vary", "Origin")

def _send(h, code, payload):
    body = json.dumps(payload, ensure_ascii=False).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(body)))
    _cors(h); h.end_headers(); h.wfile.write(body)

def _py():
    v = ROOT/".venv"/"bin"/"python"
    return str(v) if v.is_file() else sys.executable

def _argv(agent, room, prompt):
    py, agent, room = _py(), (agent or DEFAULT_AGENT).strip().lower(), (room or "R1").strip().upper()
    if agent in {"ruflo","ruflow","hive"}: return [py, str(ROOT/"tools"/"ruflo_agent.py"), "--mode", "hive", "--room", room, prompt]
    if agent == "swarm": return [py, str(ROOT/"tools"/"ruflo_agent.py"), "--mode", "swarm", "--room", room, prompt]
    if agent == "stack": return [py, str(ROOT/"tools"/"stack_agent.py"), "--room", room, prompt]
    if agent in {"agent-reach","agent_reach"}:
        r = ROOT/"tools"/"agent_reach_cli.py"
        return [py, str(r), prompt] if r.is_file() else [py, str(ROOT/"main.py"), "--execute", "--agent", "shell", "--room", room, prompt]
    if agent == "ollama": return [py, str(ROOT/"tools"/"ollama_agent.py"), prompt]
    if agent == "clip": return [py, str(ROOT/"tools"/"clip_agent.py"), prompt]
    if agent in {"shell","echo"}: return [py, str(ROOT/"tools"/"echo_agent.py"), prompt]
    return [py, str(ROOT/"main.py"), "--execute", "--agent", agent, "--room", room, prompt]

def run_agent(room, agent, prompt):
    t0 = time.time()
    agent_n = (agent or DEFAULT_AGENT).strip().lower() or DEFAULT_AGENT
    room_n = (room or "R1").strip().upper() or "R1"
    prompt_n = (prompt or "").strip()
    if not prompt_n: return {"ok": False, "error": "prompt required", "reply": "", "agent": agent_n, "room": room_n, "ms": 0}
    env = {**os.environ, "KYLA_ONLINE": "1", "CI": os.environ.get("CI", "1"), "npm_config_yes": "true"}
    try:
        proc = subprocess.run(_argv(agent_n, room_n, prompt_n), capture_output=True, text=True, timeout=TIMEOUT, cwd=str(ROOT), env=env, check=False)
        out, err = (proc.stdout or "").strip(), (proc.stderr or "").strip()
        reply = out or err or "[INFO] Agent returned no output."
        if proc.returncode and out and err: reply = out + "\n\n[stderr]\n" + err
        elif proc.returncode and not out: reply = err or f"[ERROR] agent exit {proc.returncode}"
        return {"ok": proc.returncode == 0, "reply": reply, "agent": agent_n, "room": room_n, "ms": int((time.time()-t0)*1000), "exit_code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {TIMEOUT}s", "reply": f"[ERROR] Agent timed out after {TIMEOUT}s.", "agent": agent_n, "room": room_n, "ms": int((time.time()-t0)*1000)}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "reply": f"[ERROR] Could not start agent: {exc}", "agent": agent_n, "room": room_n, "ms": int((time.time()-t0)*1000)}

def stack_snapshot():
    mapping = {"ruflo":"tools/ruflo_agent.py","ruflow":"tools/ruflo_agent.py","swarm":"tools/ruflo_agent.py","hive":"tools/ruflo_agent.py","stack":"tools/stack_agent.py","ollama":"tools/ollama_agent.py","clip":"tools/clip_agent.py","shell":"tools/echo_agent.py","echo":"tools/echo_agent.py","agent-reach":"tools/agent_reach_cli.py","agent_reach":"tools/agent_reach_cli.py"}
    agents = [{"id": n, "present": bool(mapping.get(n) and (ROOT/mapping[n]).is_file())} for n in sorted(ALLOWED)]
    try: node = subprocess.check_output(["node","-v"], text=True, timeout=5).strip()
    except Exception: node = None
    return {"ok": True, "root": str(ROOT), "default_agent": DEFAULT_AGENT, "node": node, "agents": agents, "uptime_s": int(time.time()-STARTED), "timeout_s": TIMEOUT}

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *args): sys.stderr.write("[bridge] " + (fmt % args) + "\n")
    def do_OPTIONS(self): self.send_response(204); _cors(self); self.end_headers()
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in {"/", "/v1/health"}:
            _send(self, 200, {"ok": True, "service": "kyla-online-bridge", "uptime_s": int(time.time()-STARTED), "default_agent": DEFAULT_AGENT, "supabase": _sb_on(), "hint": "POST /v1/run {room,agent,prompt}"}); return
        if path == "/v1/stack": _send(self, 200, stack_snapshot()); return
        _send(self, 404, {"ok": False, "error": "not found"})
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path != "/v1/run": _send(self, 404, {"ok": False, "error": "not found"}); return
        try:
            n = int(self.headers.get("Content-Length") or "0")
            data = json.loads((self.rfile.read(n) if n else b"{}").decode() or "{}")
            if not isinstance(data, dict): raise ValueError("JSON body must be an object")
        except (ValueError, json.JSONDecodeError) as exc:
            _send(self, 400, {"ok": False, "error": str(exc), "reply": ""}); return
        try:
            started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            prompt = str(data.get("prompt") or "")
            result = run_agent(str(data.get("room") or "R1"), str(data.get("agent") or DEFAULT_AGENT), prompt)
            _send(self, 200, result)
            if prompt.strip() and not data.get("logged_by_client"): _sb_log(result, prompt, started)
        except Exception as exc:
            _send(self, 500, {"ok": False, "error": str(exc), "reply": traceback.format_exc()[-800:]})

def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[KYLA online bridge] http://{HOST}:{PORT}  default_agent={DEFAULT_AGENT}", flush=True)
    print("  GET /v1/health  GET /v1/stack  POST /v1/run", flush=True)
    print(f"  Tunnel: cloudflared tunnel --url http://127.0.0.1:{PORT}", flush=True)
    print(f"  Supabase run log: {'on' if _sb_on() else 'off (set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)'}", flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\n[bridge] stop", flush=True); srv.shutdown()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
