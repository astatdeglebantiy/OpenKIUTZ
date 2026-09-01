import time
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import cast, Callable

import config
from server.handler import SiteRequestHandler, broadcast_live_update

def start_file_watcher():
    file_mtimes = {}

    def get_tracked_files():
        return list(config.POSTS_DIR.rglob("*.md")) + list(config.STATIC_DIR.glob("*"))

    for f in get_tracked_files():
        file_mtimes[f] = f.stat().st_mtime

    while True:
        time.sleep(0.5)
        current_files = get_tracked_files()

        for f in current_files:
            try:
                mtime = f.stat().st_mtime
                if f not in file_mtimes or mtime > file_mtimes[f]:
                    file_mtimes[f] = mtime
                    if f.suffix == ".md":
                        slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                        broadcast_live_update(slug)
                    else:
                        broadcast_live_update("")
            except Exception:
                pass


def run():
    watcher_thread = threading.Thread(target=start_file_watcher, daemon=True)
    watcher_thread.start()

    handler = cast(Callable[..., BaseHTTPRequestHandler], SiteRequestHandler)
    server = ThreadingHTTPServer((config.SERVER_HOST, config.SERVER_PORT), handler)
    server.daemon_threads = True
    print(f"Server running at http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()