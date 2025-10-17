"""
Gunicorn config - Render Starter (512MB RAM, 0.5 CPU)
"""

import os

# ===== WORKERS / THREADS =====
workers = 1
threads = int(os.environ.get("GTHREADS", "3"))  # bắt đầu 3; nâng 4 nếu cần
worker_class = "gthread"

# ===== TIMEOUTS =====
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "2"))

# ===== MEMORY LEAK GUARD =====
max_requests = int(os.environ.get("GUNICORN_MAX_REQ", "300"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_JITTER", "60"))

# ===== SOCKET =====
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = int(os.environ.get("GUNICORN_BACKLOG", "256"))

# ===== PERF / PROXY COMPAT =====
preload_app = True           # 1 worker → an toàn, warm-up nhanh
sendfile = False             # tránh lỗi với reverse proxy

# ===== LOGGING =====
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "warning")

# ===== HOOKS =====
def on_starting(server):
    print("🚀 Gunicorn starting (Render 512MB)")
    print(f"   Workers: {workers} | Threads: {threads} | Timeout: {timeout}s | Preload: {preload_app}")

def post_fork(server, worker):
    print(f"✅ Worker {worker.pid} ready")

def worker_int(worker):
    print(f"⚠️ Worker {worker.pid} received SIGINT")

def worker_abort(worker):
    print(f"❌ Worker {worker.pid} aborted (timeout/crash)")

def worker_exit(server, worker):
    print(f"👋 Worker {worker.pid} exited")