#!/usr/bin/env python3
"""
Embedding Server для Antigravity RAG.
Завантажує SentenceTransformer ОДИН РАЗ і обслуговує запити через HTTP.
Використовує вбудований http.server без додаткових залежностей.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from sentence_transformers import SentenceTransformer
import json
import time

# Load model once at startup
print("="*60)
print("EMBEDDING SERVER")
print("="*60)
print("Loading embedding model... (this takes ~30-60 seconds first time)")
start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f"✅ Model loaded in {time.time()-start:.2f}s")
print("🔥 Warming up model (first inference)...")
start = time.time()
model.encode(["warmup"])
print(f"✅ Warmup complete in {time.time()-start:.2f}s")
print("="*60)
print("Server ready on http://localhost:8001")
print("="*60)


class EmbeddingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/embed':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            texts = data.get('texts', [])
            if not texts:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No texts provided"}).encode())
                return
            
            # Generate embeddings
            embeddings = model.encode(texts).tolist()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"embeddings": embeddings}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8001), EmbeddingHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
