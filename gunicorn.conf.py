"""
Gunicorn configuration - Tối ưu cho Render Starter (512MB RAM, 0.5 CPU)
Đặt file này cùng cấp với run.py
"""

import os

# ==================== WORKER CONFIGURATION ====================
# ⚡ Giữ ở mức nhẹ: chỉ 1 worker và 2 threads để tránh OOM (Out of Memory)
workers = 1
threads = 2
worker_class = "gthread"  # Dùng thread-based để xử lý nhiều request cùng lúc nhẹ hơn fork

# ==================== TIMEOUT ====================
timeout = 90  # Giảm còn 90s để tránh giữ kết nối quá lâu
graceful_timeout = 20
keepalive = 5

# ==================== MEMORY MANAGEMENT ====================
max_requests = 500
max_requests_jitter = 30

# ==================== PRELOAD ====================
# Không preload để tránh tốn RAM khi forking (chỉ 1 worker nên không cần preload)
preload_app = False

# ==================== BINDING ====================
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# ==================== LOGGING ====================
accesslog = "-"
errorlog = "-"
loglevel = "info"

# ==================== PERFORMANCE ====================
backlog = 512  # Giảm backlog để tiết kiệm RAM

# ==================== HOOKS ====================
def on_starting(server):
    print("🚀 [Gunicorn] Starting (Render Starter mode)")
    print(f"   - Workers: {workers}")
    print(f"   - Threads: {threads}")
    print(f"   - Worker class: {worker_class}")
    print(f"   - Timeout: {timeout}s")


def post_fork(server, worker):
    print(f"✅ [Worker {worker.pid}] Spawned")


def worker_int(worker):
    print(f"⚠️ [Worker {worker.pid}] Interrupted")


def worker_abort(worker):
    print(f"❌ [Worker {worker.pid}] Aborted")


def worker_exit(server, worker):
    print(f"👋 [Worker {worker.pid}] Exited")
