#!/usr/bin/env python3
"""
Simple HTTP server for hosting the NexusAI website
"""
import http.server
import socketserver
import os

# Set the port
PORT = 8000

# Set the directory to serve files from
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create a handler with directory listing enabled
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        # Enable directory listing
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

Handler = CustomHTTPRequestHandler

if __name__ == "__main__":
    import sys
    import webbrowser
    from threading import Timer
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    def open_browser():
        webbrowser.open(f"http://localhost:{PORT}/index.html")
    Timer(1, open_browser).start()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        # Serve until process is killed
        httpd.serve_forever()
