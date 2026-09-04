from http.server import ThreadingHTTPServer
import config
from server.handler import SiteRequestHandler


def run():
    server = ThreadingHTTPServer((config.SERVER_HOST, config.SERVER_PORT), SiteRequestHandler)
    server.daemon_threads = True
    print(f"Server running at http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()
