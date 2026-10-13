# CADRIA EDIT – Windows program.
# Pokreće mali lokalni server (http://127.0.0.1) i otvara editor u Microsoft Edge-u
# (ili Google Chrome-u) kao zaseban prozor aplikacije, bez adresne trake.
# Zato sve radi isto kao u pregledaču: AI popravka, praćenje lica, export, mikrofon.
# Program se sam zatvara kad zatvorite prozor editora.
import os
import sys
import time
import shutil
import subprocess
import threading
import urllib.request
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_NAME = "CADRIA EDIT"
APP_ID = "cadria-edit-v1"
# Stalni port: podešavanja (npr. tema) vezana su za adresu, pa adresa mora uvek biti ista.
PORT = 47615
HEARTBEAT_TIMEOUT = 45  # sekundi bez znaka života od prozora -> program se gasi
STARTUP_TIMEOUT = 120   # koliko najduže čekamo da se prozor otvori

last_seen = {"t": None}


def resource_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def find_html_dir() -> Path:
    for p in (resource_dir() / "html", Path(__file__).resolve().parent.parent / "html"):
        if (p / "index.html").exists():
            return p
    raise FileNotFoundError("Nije pronađen folder 'html' sa index.html")


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
        ".bin": "application/octet-stream",
        ".svg": "image/svg+xml",
        ".png": "image/png",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/__ping"):
            last_seen["t"] = time.time()
            body = APP_ID.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


def already_running() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/__ping", timeout=2) as r:
            return r.read().decode() == APP_ID
    except Exception:
        return False


def start_server(html_dir: Path):
    handler = partial(Handler, directory=str(html_dir))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def find_browser():
    env = os.environ
    candidates = []
    for base in (env.get("PROGRAMFILES(X86)"), env.get("PROGRAMFILES"), env.get("LOCALAPPDATA")):
        if base:
            candidates.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    for base in (env.get("PROGRAMFILES"), env.get("PROGRAMFILES(X86)"), env.get("LOCALAPPDATA")):
        if base:
            candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    for c in candidates:
        if c.exists():
            return str(c)
    for name in ("msedge", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def open_window(url: str):
    browser = find_browser()
    if not browser:
        webbrowser.open(url)  # rezerva: običan pregledač
        return
    profile = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CadriaEdit" / "profil"
    profile.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([
        browser,
        f"--app={url}",
        f"--user-data-dir={profile}",
        "--window-size=1400,880",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate",
    ])


def main():
    url = f"http://127.0.0.1:{PORT}/index.html"
    if already_running():
        open_window(url)  # program već radi - samo otvori još jedan prozor
        return
    try:
        server = start_server(find_html_dir())
    except OSError:
        show_error(f"Port {PORT} je zauzet drugim programom, pa {APP_NAME} ne može da se pokrene.")
        return
    open_window(url)

    started = time.time()
    while True:
        time.sleep(2)
        seen = last_seen["t"]
        if seen is None:
            if time.time() - started > STARTUP_TIMEOUT:
                break
        elif time.time() - seen > HEARTBEAT_TIMEOUT:
            break
    server.shutdown()


def show_error(text: str):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, 0x10)
    except Exception:
        print(text)


if __name__ == "__main__":
    main()
