# CADRIA EDIT – Windows program.
# Pokreće mali lokalni server (http://127.0.0.1) i otvara editor u prozoru (Microsoft Edge WebView2).
# Snimanje fajlova (export videa, titlovi, projekat, slike) ide DIREKTNO na disk:
# Windows dijalog "Sačuvaj kao" -> editor šalje bajtove lokalnom serveru -> server upisuje u fajl.
import os
import sys
import secrets
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import webview

APP_NAME = "CADRIA EDIT"
# Stalni port: podešavanja (npr. tema) vezana su za adresu, pa adresa mora uvek biti ista.
PORTS = [47615, 47616, 47617, 47618]
TOKEN = secrets.token_urlsafe(24)
CHUNK = 1024 * 1024

FILES = {}  # id -> {"path": Path, "fh": file | None, "lock": Lock}
FILES_LOCK = threading.Lock()


def resource_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def find_html_dir() -> Path:
    for p in (resource_dir() / "html", Path(__file__).resolve().parent.parent / "html"):
        if (p / "index.html").exists():
            return p
    raise FileNotFoundError("Nije pronađen folder 'html' sa index.html")


def register_file(path) -> dict:
    path = Path(path)
    fid = secrets.token_hex(8)
    with FILES_LOCK:
        FILES[fid] = {"path": path, "fh": None, "lock": threading.Lock()}
    return {"id": fid, "name": path.name, "path": str(path)}


class Handler(SimpleHTTPRequestHandler):
    # Windows ponekad iz registra vraća pogrešan tip za .js, pa su tipovi zadati ručno.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json",
        ".wasm": "application/wasm",
        ".svg": "image/svg+xml",
        ".png": "image/png",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass

    def _reply(self, code, text=""):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        url = urlparse(self.path)
        if not url.path.startswith("/__file/"):
            return self._reply(404, "nema")
        if self.headers.get("X-Cadria-Token") != TOKEN:
            return self._reply(403, "zabranjeno")
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        entry = FILES.get(q.get("id", ""))
        if not entry:
            return self._reply(404, "nepoznat fajl")
        length = int(self.headers.get("Content-Length") or 0)
        action = url.path[len("/__file/"):]
        try:
            with entry["lock"]:
                if action == "open":
                    if entry["fh"] is None:
                        entry["path"].parent.mkdir(parents=True, exist_ok=True)
                        entry["fh"] = open(entry["path"], "w+b")
                elif action == "write":
                    fh = entry["fh"]
                    if fh is None:
                        return self._reply(409, "fajl nije otvoren")
                    fh.seek(int(q.get("pos", 0)))
                    left = length
                    while left > 0:
                        data = self.rfile.read(min(CHUNK, left))
                        if not data:
                            break
                        fh.write(data)
                        left -= len(data)
                    if left:
                        return self._reply(400, "prekinut prenos")
                elif action == "truncate":
                    if entry["fh"] is not None:
                        entry["fh"].truncate(int(q.get("size", 0)))
                elif action == "close":
                    if entry["fh"] is not None:
                        entry["fh"].flush()
                        os.fsync(entry["fh"].fileno())
                        entry["fh"].close()
                        entry["fh"] = None
                else:
                    return self._reply(404, "nepoznata radnja")
        except OSError as e:
            return self._reply(500, str(e))
        # preostali bajtovi tela (ako ih ima) se pročitaju da veza ostane ispravna
        if action != "write" and length:
            self.rfile.read(length)
        return self._reply(200, "ok")


class Api:
    """Funkcije koje editor poziva preko window.pywebview.api"""

    def __init__(self):
        self.window = None
        videos = Path.home() / "Videos"
        self.last_dir = videos if videos.is_dir() else Path.home()

    def get_token(self):
        return TOKEN

    def ask_save(self, suggested_name, exts):
        exts = [e.lower().lstrip(".") for e in (exts or []) if e]
        types = tuple(f"{e.upper()} fajl (*.{e})" for e in dict.fromkeys(exts)) + ("Svi fajlovi (*.*)",)
        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=str(self.last_dir),
            save_filename=suggested_name or "fajl",
            file_types=types,
        )
        if not result:
            return None
        path = Path(result[0] if isinstance(result, (list, tuple)) else result)
        if exts and path.suffix.lower().lstrip(".") not in exts:
            path = path.with_name(path.name + "." + exts[0])
        self.last_dir = path.parent
        return register_file(path)

    def reveal(self, fid):
        entry = FILES.get(fid)
        if entry and sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(entry["path"])])


def start_server(html_dir: Path) -> int:
    handler = partial(Handler, directory=str(html_dir))
    for port in PORTS + [0]:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        except OSError:
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server.server_address[1]
    raise OSError("Nije moguće pokrenuti lokalni server")


def show_error(text: str):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, 0x10)
    except Exception:
        print(text)


def main():
    port = start_server(find_html_dir())
    url = f"http://127.0.0.1:{port}/index.html"

    api = Api()
    webview.settings["ALLOW_DOWNLOADS"] = True  # rezerva, ako nešto ipak ide kao preuzimanje
    api.window = webview.create_window(
        APP_NAME,
        url,
        js_api=api,
        width=1400,
        height=880,
        min_size=(960, 620),
        text_select=True,
        background_color="#111111",
    )

    storage = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CadriaEdit"
    storage.mkdir(parents=True, exist_ok=True)
    try:
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(storage))
    except Exception as e:
        show_error(
            "CADRIA EDIT ne može da se pokrene jer na računaru nedostaje "
            "Microsoft Edge WebView2 Runtime.\n\n"
            "Preuzmite ga besplatno sa Microsoft sajta (potražite „WebView2 Runtime“), "
            "instalirajte i ponovo pokrenite program.\n\n"
            f"Detalji: {e}"
        )


if __name__ == "__main__":
    main()
