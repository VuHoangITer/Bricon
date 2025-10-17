import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Config tối ưu cho Render Starter (512MB RAM, 0.5 CPU) — đồng bộ Gunicorn"""

    # ===== CƠ BẢN =====
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # ===== DATABASE =====
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app.db')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== ĐỒNG BỘ THREADS/POOL VỚI GUNICORN =====
    # Gunicorn: workers=1, threads=int(env GTHREADS, mặc định 3)
    THREADS = int(os.environ.get('GTHREADS', 3))      # khớp gunicorn.conf.py
    POOL_PER_WORKER = int(os.environ.get('DB_POOL_PER_WORKER', min(THREADS, 3)))  # ≈ threads nhưng giới hạn 3
    MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 1))

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': POOL_PER_WORKER,     # 1 worker → tổng connection ≈ pool_size (+ overflow)
        'max_overflow': MAX_OVERFLOW,
        'pool_recycle': 600,              # 10 phút
        'pool_pre_ping': True,
        'pool_timeout': 20,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'briconvn_app',
            'options': '-c statement_timeout=45000'   # < gunicorn timeout (60s)
        },
        'echo_pool': os.environ.get('FLASK_ENV') == 'development'
    }

    # ===== UPLOAD =====
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'ico', 'svg'}

    # ===== PAGINATION =====
    POSTS_PER_PAGE = 12
    BLOGS_PER_PAGE = 9

    # ===== SEO =====
    SITE_NAME = 'Briconvn'
    SITE_DESCRIPTION = 'Doanh nghiệp chuyên sản xuất và phân phối keo dán gạch, keo chả ron & chống thấm'

    # ===== GEMINI CHATBOT (khớp timeout tổng thể 60s của Gunicorn) =====
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHATBOT_ENABLED = True
    CHATBOT_REQUEST_LIMIT = int(os.environ.get('CHATBOT_REQUEST_LIMIT', 15))
    CHATBOT_REQUEST_WINDOW = int(os.environ.get('CHATBOT_REQUEST_WINDOW', 3600))  # 1h
    GEMINI_TIMEOUT = int(os.environ.get('GEMINI_TIMEOUT', 30))  # ≤ 45s để còn headroom dưới gunicorn 60s

    # (Tuỳ chọn hybrid prompt)
    CHATBOT_HISTORY_TURNS = int(os.environ.get('CHATBOT_HISTORY_TURNS', 5))
    CHATBOT_PROMPT_MODE_DEFAULT = os.environ.get('CHATBOT_PROMPT_MODE_DEFAULT', 'lite')
    CHATBOT_TEMPERATURE = float(os.environ.get('CHATBOT_TEMPERATURE', 0.6))
    CHATBOT_MAX_OUTPUT_TOKENS = int(os.environ.get('CHATBOT_MAX_OUTPUT_TOKENS', 800))
    HOTLINE_ZALO = os.environ.get('HOTLINE_ZALO', '0901.180.094')

    # ===== FLASK-COMPRESS =====
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

    # ===== CACHING =====
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # ===== SECURITY / RATE LIMIT =====
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 phút

    @staticmethod
    def init_app(app):
        import logging
        from logging.handlers import RotatingFileHandler
        if not app.debug:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(
                'logs/briconvn.log',
                maxBytes=512 * 1024,
                backupCount=2
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.ERROR)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.ERROR)
            app.logger.info('Briconvn startup')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    GEMINI_TIMEOUT = int(os.environ.get('GEMINI_TIMEOUT', 30))

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging, sys
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.ERROR)
        app.logger.addHandler(stream_handler)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
