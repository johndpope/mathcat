"""HTTP service. Binds to 127.0.0.1 unless --host says otherwise.

GET  /health
GET  /png?tex=...&dpi=220&color=%23f2f2f7&bg=transparent
POST /png    {"tex": "...", "dpi": 220, "color": "#f2f2f7", "bg": null}
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from mathcat.render import FormulaError, render_png

_MAX_BODY = 64 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "mathd/0.1"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {"ok": True, "service": "mathd"})
            return
        if parsed.path in {"/", ""}:
            self._text(
                200,
                "mathd\n"
                "GET /health\n"
                "GET /png?tex=...\n"
                "POST /png  {\"tex\": \"...\"}\n",
            )
            return
        if parsed.path != "/png":
            self._json(404, {"error": "not found"})
            return
        query = parse_qs(parsed.query)
        tex = query.get("tex", [""])[0]
        self._render(
            tex,
            dpi=_optional_int(query.get("dpi", [None])[0]),
            color=query.get("color", [None])[0],
            bg=query.get("bg", [None])[0],
        )

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/png":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > _MAX_BODY:
            self._json(400, {"error": "body too large"})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "body must be JSON"})
            return
        if not isinstance(payload, dict):
            self._json(400, {"error": "body must be a JSON object"})
            return
        self._render(
            str(payload.get("tex", "")),
            dpi=payload.get("dpi"),
            color=payload.get("color"),
            bg=payload.get("bg"),
        )

    def _render(self, tex: str, dpi, color, bg) -> None:
        kwargs = {}
        if dpi is not None:
            if not isinstance(dpi, int) or isinstance(dpi, bool):
                self._json(400, {"error": "dpi must be an integer"})
                return
            kwargs["dpi"] = dpi
        if color:
            kwargs["color"] = str(color)
        if bg is not None:
            kwargs["bg"] = None if bg in ("", "transparent", None) else str(bg)
        try:
            png = render_png(tex, **kwargs)
        except FormulaError as exc:
            self._json(400, {"error": str(exc)})
            return
        self._bytes(200, "image/png", png)

    def _json(self, status: int, payload: dict) -> None:
        self._bytes(status, "application/json", json.dumps(payload).encode("utf-8"))

    def _text(self, status: int, text: str) -> None:
        self._bytes(status, "text/plain; charset=utf-8", text.encode("utf-8"))

    def _bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _optional_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def serve(host: str, port: int) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"mathd listening on http://{host}:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mathd", description="Serve math formula PNGs on localhost.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
