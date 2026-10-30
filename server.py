import http.server
import socketserver
import sys
import os
import mimetypes

# Set directory to this script's directory (root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Register modern web MIME types
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('font/woff2', '.woff2')

PORT = 8000
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        pass

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        if self.path == '/api/searches':
            try:
                import json
                searches_path = os.path.join(BASE_DIR, 'data', 'searches.json')
                cur = {"summary": {}, "recent": []}
                if os.path.exists(searches_path):
                    with open(searches_path, 'r', encoding='utf-8') as f:
                        cur = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store, no-cache')
                self.end_headers()
                self.wfile.write(json.dumps(cur).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return
        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path in ['/api/update-product', '/api/save-products']:
            try:
                import json
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8')
                data = json.loads(post_body)
                
                prod_path = os.path.join(BASE_DIR, 'data', 'products.json')
                test_prod_path = os.path.join(BASE_DIR, 'test design site', 'data', 'products.json')

                if self.path == '/api/update-product':
                    prod_id = data.get('id')
                    updates = data.get('updates', {})
                    if os.path.exists(prod_path):
                        with open(prod_path, 'r', encoding='utf-8') as f:
                            products = json.load(f)
                        found = False
                        for p in products:
                            if p.get('id') == prod_id:
                                p.update(updates)
                                found = True
                                break
                        if not found and updates:
                            products.insert(0, updates)
                        with open(prod_path, 'w', encoding='utf-8') as f:
                            json.dump(products, f, indent=2, ensure_ascii=False)
                        if os.path.exists(os.path.dirname(test_prod_path)):
                            with open(test_prod_path, 'w', encoding='utf-8') as f:
                                json.dump(products, f, indent=2, ensure_ascii=False)
                elif self.path == '/api/save-products':
                    if isinstance(data, list):
                        with open(prod_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        if os.path.exists(os.path.dirname(test_prod_path)):
                            with open(test_prod_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        elif self.path in ['/api/log-search', '/api/clear-searches']:
            try:
                import json
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
                data = json.loads(post_body) if post_body else {}

                searches_path = os.path.join(BASE_DIR, 'data', 'searches.json')
                if self.path == '/api/clear-searches':
                    with open(searches_path, 'w', encoding='utf-8') as f:
                        json.dump({"summary": {}, "recent": []}, f, indent=2, ensure_ascii=False)
                elif self.path == '/api/log-search':
                    query = str(data.get('query', '')).strip().lower()
                    if query:
                        cur = {"summary": {}, "recent": []}
                        if os.path.exists(searches_path):
                            try:
                                with open(searches_path, 'r', encoding='utf-8') as f:
                                    cur = json.load(f)
                            except Exception:
                                pass
                        if not isinstance(cur, dict):
                            cur = {"summary": {}, "recent": []}
                        if "summary" not in cur: cur["summary"] = {}
                        if "recent" not in cur: cur["recent"] = []

                        entry = cur["summary"].get(query, {
                            "query": query,
                            "count": 0,
                            "resultsCount": data.get("resultsCount", 0),
                            "topProduct": data.get("topProduct", ""),
                            "lastSearched": ""
                        })
                        entry["count"] = entry.get("count", 0) + 1
                        entry["lastSearched"] = data.get("timestamp") or ""
                        if data.get("resultsCount") is not None:
                            entry["resultsCount"] = data.get("resultsCount")
                        if data.get("topProduct"):
                            entry["topProduct"] = data.get("topProduct")
                        cur["summary"][query] = entry

                        cur["recent"].insert(0, {
                            "query": query,
                            "resultsCount": data.get("resultsCount", 0),
                            "topProduct": data.get("topProduct", ""),
                            "timestamp": data.get("timestamp") or ""
                        })
                        cur["recent"] = cur["recent"][:200]

                        with open(searches_path, 'w', encoding='utf-8') as f:
                            json.dump(cur, f, indent=2, ensure_ascii=False)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        self.send_response(404)
        self.end_headers()

class ThreadedHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_server():
    port = PORT
    max_port = port + 20
    httpd = None

    while port <= max_port:
        try:
            httpd = ThreadedHTTPServer(("", port), NoCacheHandler)
            break
        except OSError as e:
            if port < max_port:
                port += 1
            else:
                raise e

    print(f"==================================================")
    print(f" HRz Pitstop Main Site Server Running")
    print(f" Local URL: http://localhost:{port}/")
    print(f" Root Directory: {BASE_DIR}")
    print(f" Multi-threaded: Enabled (parallel asset loading)")
    print(f" Cache: Disabled (no-store, no-cache)")
    print(f"==================================================")
    sys.stdout.flush()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
