from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_compress import Compress  # 🔥 THÊM
from app.config import Config
import cloudinary
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import pytz

# Khởi tạo extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
compress = Compress()  # 🔥 THÊM: Nén response

# Định nghĩa timezone Việt Nam
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


def create_app(config_class=Config):
    """Factory function để tạo Flask app - Tối ưu cho Render"""
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # ==================== CONFIGURATION ====================
    app.config.from_object(config_class)
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
    app.config['CHATBOT_ENABLED'] = True

    # ==================== INIT EXTENSIONS ====================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    compress.init_app(app)  # 🔥 Bật compression

    # ==================== CLOUDINARY - SIMPLE CONFIG ====================
    # 🔥 TỐI ƯU: Đơn giản hóa config, bỏ phần parse phức tạp
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )

    # ==================== FLASK-LOGIN ====================
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'

    # ==================== REGISTER BLUEPRINTS ====================
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.chatbot import chatbot_bp
    from app.quiz import quiz_bp, quiz_admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(quiz_admin_bp)

    # ==================== GEMINI INIT ====================
    with app.app_context():
        from app.chatbot.routes import init_gemini
        init_gemini()

    # Khởi tạo cấu hình
    config_class.init_app(app)

    # ==================== CONTEXT PROCESSOR - HỢP NHẤT ====================
    # 🔥 TỐI ƯU: Gộp 2 context processors thành 1 để tránh duplicate queries
    @app.context_processor
    def inject_globals():
        """
        Inject các biến toàn cục vào tất cả templates
        ⚠️ CHÚ Ý: Function này chạy cho MỌI request → phải nhanh
        """
        from app.models import Category, get_setting
        from datetime import datetime

        # 🔥 TỐI ƯU: Cache categories trong g object (per-request cache)
        from flask import g
        if not hasattr(g, 'all_categories'):
            g.all_categories = Category.query.filter_by(is_active=True).all()

        return {
            'get_setting': get_setting,
            'site_name': app.config.get('SITE_NAME', 'Briconvn'),
            'all_categories': g.all_categories,
            'current_year': datetime.now().year,
            # Pre-load settings thường dùng
            'primary_color': get_setting('primary_color', '#ffc107'),
            'default_banner': get_setting('default_banner', ''),
            'per_page': int(get_setting('default_posts_per_page', '12')),
        }

    # ==================== JINJA2 FILTERS ====================
    @app.template_filter('format_price')
    def format_price(value):
        """Format giá tiền: 1000000 -> 1.000.000"""
        if value:
            return '{:,.0f}'.format(value).replace(',', '.')
        return '0'

    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to <br> tags"""
        if not text:
            return ''
        return text.replace('\n', '<br>\n')

    # ==================== TIMEZONE FILTERS ====================
    @app.template_filter('vn_datetime')
    def vn_datetime_filter(dt, format='%d/%m/%Y %H:%M:%S'):
        """Chuyển UTC datetime sang múi giờ Việt Nam"""
        if dt is None:
            return ''
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        vn_dt = dt.astimezone(VN_TZ)
        return vn_dt.strftime(format)

    @app.template_filter('vn_date')
    def vn_date_filter(dt):
        """Chỉ hiển thị ngày"""
        return vn_datetime_filter(dt, '%d/%m/%Y')

    @app.template_filter('vn_time')
    def vn_time_filter(dt):
        """Chỉ hiển thị giờ"""
        return vn_datetime_filter(dt, '%H:%M:%S')

    @app.template_filter('vn_datetime_friendly')
    def vn_datetime_friendly_filter(dt):
        """Hiển thị thời gian dễ đọc: 13/10/2025 lúc 14:30"""
        return vn_datetime_filter(dt, '%d/%m/%Y lúc %H:%M')

    # ==================== ERROR HANDLERS ====================
    # 🔥 THÊM: Xử lý lỗi để tránh crash
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()  # Rollback để tránh stale session
        return render_template('500.html'), 500

    return app