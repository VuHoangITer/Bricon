import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()


class Config:
    """Cấu hình tối ưu cho Render Starter (512MB RAM, 0.5 CPU)"""

    # ==================== CƠ BẢN ====================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # ==================== DATABASE - TỐI ƯU QUAN TRỌNG ====================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app.db')

    # Fix lỗi với Render PostgreSQL URL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔥 TỐI ƯU QUAN TRỌNG: Connection Pool cho môi trường hạn chế
    # Render Starter chỉ cho phép ~20 connections đồng thời
    # 2 workers × 3 pool_size = 6 connections (an toàn)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 3,  # Giảm từ 5 xuống 3 connections/worker
        'pool_recycle': 300,  # Recycle connection sau 5 phút (tránh "server closed connection")
        'pool_pre_ping': True,  # Kiểm tra connection trước khi dùng (tránh stale connections)
        'max_overflow': 1,  # Chỉ cho phép thêm 1 connection tạm thời
        'pool_timeout': 10,  # Timeout 10s khi chờ connection (tránh deadlock)
        'connect_args': {
            'connect_timeout': 10,  # Timeout khi kết nối database
            'options': '-c statement_timeout=30000'  # Query timeout 30s
        }
    }

    # ==================== UPLOAD FILE ====================
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # Giảm kích thước upload để tiết kiệm RAM khi xử lý
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Giảm từ 16MB xuống 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'ico', 'svg'}  # Bỏ ico, svg nếu không dùng

    # ==================== PAGINATION ====================
    POSTS_PER_PAGE = 12
    BLOGS_PER_PAGE = 9

    # ==================== SEO ====================
    SITE_NAME = 'Briconvn'
    SITE_DESCRIPTION = 'Doanh nghiệp chuyên sản xuất và phân phối keo dán gạch, keo chả ron & chống thấm'

    # ==================== GEMINI CHATBOT ====================
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHATBOT_REQUEST_LIMIT = 20
    CHATBOT_REQUEST_WINDOW = 7200
    CHATBOT_ENABLED = True

    # 🔥 THÊM: Timeout cho Gemini API (tránh block vô thời hạn)
    GEMINI_TIMEOUT = 15  # 15 giây timeout

    # ==================== FLASK-COMPRESS ====================
    # Nén response để giảm băng thông
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript'
    ]
    COMPRESS_LEVEL = 6  # Cân bằng giữa tốc độ và tỷ lệ nén
    COMPRESS_MIN_SIZE = 500  # Chỉ nén response > 500 bytes

    # ==================== CACHING ====================
    # Simple in-memory cache (không dùng Redis để tiết kiệm)
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # Cache 5 phút

    # ==================== SECURITY ====================
    # Giới hạn request để tránh bị spam
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'  # In-memory rate limiting

    @staticmethod
    def init_app(app):
        """Khởi tạo cấu hình cho app"""
        # ⚠️ BỎ PHẦN TẠO THỦ CÔNG: Cloudinary xử lý, không cần local uploads
        # Chỉ tạo folder nếu thực sự cần (ví dụ: temp files)

        # Logging cho production
        import logging
        from logging.handlers import RotatingFileHandler

        if not app.debug:
            # File handler với rotation để tránh log quá lớn
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(
                'logs/briconvn.log',
                maxBytes=1024 * 1024,  # 1MB
                backupCount=3  # Giữ 3 file backup
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Briconvn startup')


class DevelopmentConfig(Config):
    """Cấu hình cho môi trường development"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log tất cả SQL queries


class ProductionConfig(Config):
    """Cấu hình cho production (Render)"""
    DEBUG = False
    SQLALCHEMY_ECHO = False  # Tắt SQL logging để tiết kiệm I/O

    # Tăng timeout cho production
    GEMINI_TIMEOUT = 20


# Chọn config dựa trên environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': Config
}