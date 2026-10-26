import os, subprocess, json, hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("KYLA_API_TOKEN", "")
def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-2000:]}
class H(BaseHTTPRequestHandler):
    def _auth(self):
        return hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN)
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path == "/health":
            return self._json({"status": "ok", "service": "kyla-api"})
        return self._json({"error": "not found"}, 404)
    def do_POST(self):
        if not TOKEN or not self._auth():
            return self._json({"error": "unauthorized"}, 401)
        routes = {
            "/api/quant": ["node", "kyla/kyla-quant.js"],
            "/api/news": ["node", "kyla/kyla-news.js"],
            "/api/stats": ["node", "kyla/kyla-stats.js"],
            "/api/backtest": [str(ROOT / ".venv/bin/python"), "trading/backtest.py", "--csv", "data/XAUUSD_M5.csv", "--symbol", "XAUUSD", "--config", "trading/config.yaml", "--output", "result.json"],
        }
        if self.path in routes:
            return self._json(run(routes[self.path]))
        return self._json({"error": "not found"}, 404)
if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
