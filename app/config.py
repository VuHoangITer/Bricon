import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()


class Config:
    """Cấu hình chung cho ứng dụng Flask"""

    # Secret key để mã hóa session và form CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Cấu hình database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app.db')

    # Fix lỗi với Render PostgreSQL URL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cấu hình upload file
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'ico', 'svg'}

    # Pagination
    POSTS_PER_PAGE = 12
    BLOGS_PER_PAGE = 9

    # SEO
    SITE_NAME = 'Hoangvn'
    SITE_DESCRIPTION = 'Website doanh nghiệp chuyên nghiệp'

    # ========== THÊM MỚI: GEMINI CHATBOT CONFIGURATION ==========
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHATBOT_REQUEST_LIMIT = 20  # Giới hạn 20 tin nhắn/giờ
    CHATBOT_REQUEST_WINDOW = 7200  # 1 giờ (tính bằng giây)
    CHATBOT_ENABLED = True  # Bật/tắt chatbot

    @staticmethod
    def init_app(app):
        """Khởi tạo cấu hình cho app"""
        # Tạo thư mục upload nếu chưa tồn tại
        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        # Tạo các thư mục con
        for folder in ['products', 'banners', 'blogs', 'categories', 'albums']:
            os.makedirs(os.path.join(upload_folder, folder), exist_ok=True)