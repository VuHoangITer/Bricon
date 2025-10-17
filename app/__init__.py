from flask import Flask, g, request  # ✅ thêm request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_compress import Compress
from app.config import Config
import cloudinary
import os
from dotenv import load_dotenv
import pytz

# Khởi tạo extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
compress = Compress()

# Timezone Việt Nam
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

# ===== CACHE GLOBAL (TTL) =====
_CATEGORIES_CACHE = None
_CACHE_TIMESTAMP = None
_CACHE_TTL = 300  # 5 phút


def create_app(config_class=Config):
    """Factory function để tạo Flask app - Tối ưu cho Render"""
    app = Flask(__name__)
    load_dotenv()

    # ==================== CONFIG ====================
    app.config.from_object(config_class)
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
    app.config['CHATBOT_ENABLED'] = True

    # ==================== INIT EXTENSIONS ====================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    compress.init_app(app)  # ✅ bật nén HTTP

    # ==================== CLOUDINARY ====================
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

    # Khởi tạo cấu hình logging, v.v.
    config_class.init_app(app)

    # ==================== CONTEXT PROCESSOR (TTL + per-request g) ====================
    @app.context_processor
    def inject_globals():
        """
        - TTL cache (process-level) 5 phút để tránh query lặp qua nhiều request
        - Per-request cache bằng g.* để 1 request không query lại
        """
        from app.models import get_setting, Category
        from datetime import datetime
        import time

        global _CATEGORIES_CACHE, _CACHE_TIMESTAMP

        # per-request guard
        if not hasattr(g, 'all_categories'):
            now = time.time()
            need_refresh = (
                _CATEGORIES_CACHE is None or
                _CACHE_TIMESTAMP is None or
                (now - _CACHE_TIMESTAMP) > _CACHE_TTL
            )
            if need_refresh:
                _CATEGORIES_CACHE = Category.query.filter_by(is_active=True).all()
                _CACHE_TIMESTAMP = now
            g.all_categories = _CATEGORIES_CACHE  # dùng cache process-level

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
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('500.html'), 500

    # Render đôi khi trả 502/503 khi cold start/quá tải
    @app.errorhandler(502)
    @app.errorhandler(503)
    def service_unavailable(error):
        from flask import render_template
        return render_template('500.html'), 503

    # ==================== BEFORE/AFTER/TEARDOWN ====================
    @app.before_request
    def before_request():
        # pool_pre_ping đã xử lý stale connections
        pass

    @app.after_request
    def after_request(response):
        """
        - Cache static mạnh tay
        - Thêm security headers cơ bản
        """
        if request.path.startswith('/static/'):
            response.cache_control.max_age = 31536000  # 1 năm
            response.cache_control.public = True

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Đảm bảo đóng session sau mỗi request"""
        db.session.remove()

    return app


# ==================== CLEAR CACHE FUNCTION ====================
def clear_categories_cache():
    """Helper function để clear cache khi cần"""
    global _CATEGORIES_CACHE, _CACHE_TIMESTAMP
    _CATEGORIES_CACHE = None
    _CACHE_TIMESTAMP = None
