"""Local clinician workspace: serves the page and records human review decisions.

    python -m backend.app [--run data/runs/<dir>] [--port 8000]

Stdlib only; binds to 127.0.0.1. It calls NO language model. The only write it performs is appending a
record-only review decision (backend/review/records.py) beside the run.
"""
import argparse
import glob
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend import config
from backend.review import records
from backend.viewer.build_viewer import render

MAX_BODY = 20_000


def review_state(run_dir: Path) -> dict:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    reviews = records.read_reviews(run_dir)
    return {"reviews": reviews, "review_integrity": records.check(run_dir),
            "review_status": records.status_by_item(run, reviews)}


def make_server(run_dir: Path, port: int = 8000) -> ThreadingHTTPServer:
    run_dir = Path(run_dir)
    lock = threading.Lock()
    page = render(run_dir, server=True).encode("utf-8")
    allowed_hosts = set()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # keep the console quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, page, "text/html")
            elif self.path == "/api/reviews":
                self._json(200, review_state(run_dir))
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/review":
                return self._json(404, {"error": "not found"})
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if host not in allowed_hosts:  # blocks DNS-rebinding: only the literal local address is accepted
                return self._json(403, {"error": "unexpected Host header"})
            if origin and origin.split("://", 1)[-1] != host:
                return self._json(403, {"error": "cross-origin request refused"})
            if "application/json" not in self.headers.get("Content-Type", ""):
                return self._json(415, {"error": "send JSON"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._json(400, {"error": "invalid Content-Length"})
            if n <= 0 or n > MAX_BODY:
                return self._json(413, {"error": "request body missing or too large"})
            try:
                b = json.loads(self.rfile.read(n))
                args = [str(b.get(k, "")) for k in ("item", "decision", "reviewer", "role", "reason")]
            except (ValueError, AttributeError):
                return self._json(400, {"error": "invalid JSON"})
            try:
                with lock:
                    records.record(run_dir, *args)
            except records.ReviewError as e:
                return self._json(400, {"error": str(e)})
            self._json(200, review_state(run_dir))

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    p = srv.server_address[1]
    allowed_hosts.update({f"127.0.0.1:{p}", f"localhost:{p}"})
    return srv


def main() -> int:
    ap = argparse.ArgumentParser(prog="python -m backend.app")
    ap.add_argument("--run", default=None)
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    run_dir = Path(a.run) if a.run else Path(sorted(glob.glob(str(config.ROOT / "data" / "runs" / "*-live")))[-1])
    srv = make_server(run_dir, a.port)
    print(f"Clinician workspace for run {run_dir.name}: http://127.0.0.1:{srv.server_address[1]}/  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
