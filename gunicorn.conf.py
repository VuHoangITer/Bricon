"""
Gunicorn configuration file - Tối ưu cho Render Starter (512MB RAM)
Đặt file này cùng cấp với run.py
"""

import os
import multiprocessing

# ==================== WORKER CONFIGURATION ====================
# 🔥 TỐI ƯU: Chỉ dùng 2 workers cho 512MB RAM
# Công thức: (2 × CPU cores) + 1 = (2 × 0.5) + 1 ≈ 2 workers
workers = 2

# Threads per worker (tăng concurrency mà không tốn nhiều RAM)
threads = 2

# Worker class
worker_class = 'sync'  # hoặc 'gthread' nếu muốn thread-based

# ==================== TIMEOUT ====================
# Timeout cho requests (giây)
timeout = 120  # 2 phút cho requests chậm (chatbot, AI)
graceful_timeout = 30  # Thời gian để worker shutdown gracefully
keepalive = 5  # Keep-alive timeout

# ==================== MEMORY MANAGEMENT ====================
# Restart worker sau N requests để tránh memory leak
max_requests = 1000
max_requests_jitter = 50  # Random jitter để tránh restart đồng thời

# ==================== PRELOAD ====================
# Preload app trước khi fork workers (tiết kiệm RAM)
preload_app = True

# ==================== BINDING ====================
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# ==================== LOGGING ====================
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'

# ==================== PERFORMANCE ====================
# Backlog queue size
backlog = 2048

# Worker connections (cho async workers)
# worker_connections = 1000  # Chỉ dùng nếu worker_class = 'gevent' hoặc 'eventlet'

# ==================== HOOKS ====================
def on_starting(server):
    """Chạy khi Gunicorn khởi động"""
    print("🚀 [Gunicorn] Starting with:")
    print(f"   - Workers: {workers}")
    print(f"   - Threads/worker: {threads}")
    print(f"   - Timeout: {timeout}s")
    print(f"   - RAM limit: ~512MB")


def worker_int(worker):
    """Xử lý khi worker bị interrupt"""
    print(f"⚠️ [Worker {worker.pid}] Interrupted")


def worker_abort(worker):
    """Xử lý khi worker bị abort"""
    print(f"❌ [Worker {worker.pid}] Aborted")


def post_fork(server, worker):
    """Chạy sau khi fork worker mới"""
    print(f"✅ [Worker {worker.pid}] Spawned")


def pre_fork(server, worker):
    """Chạy trước khi fork worker"""
    pass


def worker_exit(server, worker):
    """Chạy khi worker exit"""
    print(f"👋 [Worker {worker.pid}] Exited")