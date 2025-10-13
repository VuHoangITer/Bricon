# ==================== USER MODEL ====================
# ==================== THAY ĐỔI CLASS USER TRONG app/models.py ====================

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime


class User(db.Model, UserMixin):
    """Model cho người dùng với RBAC"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))

    # ✅ THAY ĐỔI: Thêm role_id (foreign key)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=None)

    # ✅ GIỮ LẠI: is_admin (deprecated field cho tương thích ngược)
    # Khi migrate, chuyển users cũ: is_admin=True → role_id=1 (admin)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    blogs = db.relationship('Blog', backref='author_obj', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash và lưu mật khẩu"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Kiểm tra mật khẩu"""
        return check_password_hash(self.password_hash, password)

    # ==================== RBAC METHODS ====================

    # ✅ THÊM: TIMEZONE PROPERTIES
    @property
    def created_at_vn(self):
        """Lấy created_at theo múi giờ Việt Nam"""
        from app.utils import utc_to_vn
        return utc_to_vn(self.created_at)

    @property
    def updated_at_vn(self):
        """Lấy updated_at theo múi giờ Việt Nam"""
        from app.utils import utc_to_vn
        return utc_to_vn(self.updated_at)

    @property
    def is_admin(self):
        """
        Backward compatibility với code cũ
        Trả về True nếu role là 'admin'
        """
        return self.role_obj and self.role_obj.name == 'admin'

    @property
    def role_name(self):
        """Lấy tên role (admin, editor, moderator, user)"""
        return self.role_obj.name if self.role_obj else 'user'

    @property
    def role_display_name(self):
        """Lấy tên hiển thị role (Quản trị viên, Biên tập viên, ...)"""
        return self.role_obj.display_name if self.role_obj else 'Người dùng'

    @property
    def role_color(self):
        """Lấy màu badge role (danger, primary, info, secondary)"""
        return self.role_obj.color if self.role_obj else 'secondary'

    def has_permission(self, permission_name):
        """
        Kiểm tra user có quyền cụ thể không

        Args:
            permission_name (str): Tên permission (vd: 'manage_products')

        Returns:
            bool: True nếu có quyền
        """
        if not self.role_obj or not self.is_active:
            return False
        return self.role_obj.has_permission(permission_name)

    def has_any_permission(self, *permission_names):
        """
        Kiểm tra user có ít nhất 1 trong các quyền

        Args:
            *permission_names: Danh sách tên permissions

        Returns:
            bool: True nếu có ít nhất 1 quyền
        """
        return any(self.has_permission(perm) for perm in permission_names)

    def has_all_permissions(self, *permission_names):
        """
        Kiểm tra user có tất cả các quyền

        Args:
            *permission_names: Danh sách tên permissions

        Returns:
            bool: True nếu có đủ tất cả quyền
        """
        return all(self.has_permission(perm) for perm in permission_names)

    def get_permissions(self):
        """
        Lấy danh sách tất cả permissions của user

        Returns:
            list: Danh sách Permission objects
        """
        if not self.role_obj:
            return []
        return self.role_obj.permissions.filter_by(is_active=True).all()

    def assign_role(self, role_name):
        """
        Gán role cho user

        Args:
            role_name (str): Tên role (admin, editor, moderator, user)
        """
        from app.models_rbac import Role
        role = Role.query.filter_by(name=role_name).first()
        if role:
            self.role_id = role.id
            return True
        return False


# ==================== USER LOADER ====================
from app import login_manager


@login_manager.user_loader
def load_user(user_id):
    """Load user cho Flask-Login"""
    return User.query.get(int(user_id))


# ==================== CATEGORY MODEL ====================
class Category(db.Model):
    """Model danh mục sản phẩm"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship với Product
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


# ==================== PRODUCT MODEL ====================
class Product(db.Model):
    """Model sản phẩm"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0)
    old_price = db.Column(db.Float)
    image = db.Column(db.String(255))
    images = db.Column(db.Text)  # JSON string chứa nhiều ảnh
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image_alt_text = db.Column(db.String(255))
    image_title = db.Column(db.String(255))
    image_caption = db.Column(db.Text)

    # Thông tin kỹ thuật - Lưu dạng JSON
    composition = db.Column(db.JSON)  # Thành phần: list hoặc string
    production = db.Column(db.Text)  # Quy trình sản xuất
    application = db.Column(db.JSON)  # Ứng dụng: list
    expiry = db.Column(db.String(200))  # Hạn sử dụng
    packaging = db.Column(db.String(500))  # Quy cách đóng gói
    colors = db.Column(db.JSON)  # Màu sắc: list
    technical_specs = db.Column(db.JSON)  # Thông số kỹ thuật: dict
    standards = db.Column(db.String(200))  # Tiêu chuẩn

    def __repr__(self):
        return f'<Product {self.name}>'


# ==================== BANNER MODEL ====================
class Banner(db.Model):
    """Model banner slider trang chủ"""
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(255))
    image = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    button_text = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f'<Banner {self.title}>'


# ==================== BLOG MODEL ====================
class Blog(db.Model):
    """Model tin tức / blog với SEO optimization"""
    __tablename__ = 'blogs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.Column(db.String(100))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Legacy image SEO fields (giữ lại để tương thích)
    image_alt_text = db.Column(db.String(255))
    image_title = db.Column(db.String(255))
    image_caption = db.Column(db.Text)

    # ✅ THÊM CÁC TRƯỜNG SEO MỚI
    meta_title = db.Column(db.String(70))  # SEO title tag (50-60 ký tự tối ưu)
    meta_description = db.Column(db.String(160))  # Meta description (120-160 ký tự)
    meta_keywords = db.Column(db.String(255))  # Keywords (optional, ít quan trọng)
    focus_keyword = db.Column(db.String(100))  # Từ khóa chính để tính SEO score

    # Reading metrics
    reading_time = db.Column(db.Integer)  # Thời gian đọc ước tính (phút)
    word_count = db.Column(db.Integer)  # Số từ trong bài viết

    # SEO Score tracking
    seo_score = db.Column(db.Integer, default=0)
    seo_grade = db.Column(db.String(5), default='F')
    seo_last_checked = db.Column(db.DateTime)

    def calculate_reading_time(self):
        """Tính thời gian đọc dựa trên số từ (200 từ/phút)"""
        if self.content:
            from html import unescape
            import re
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', '', self.content)
            text = unescape(text)
            words = len(text.split())
            self.word_count = words
            self.reading_time = max(1, round(words / 200))
        else:
            self.word_count = 0
            self.reading_time = 1

    def update_seo_score(self):
        """Tính và lưu điểm SEO vào database"""
        from app.admin.routes import calculate_blog_seo_score
        result = calculate_blog_seo_score(self)
        self.seo_score = result['score']
        self.seo_grade = result['grade']
        self.seo_last_checked = datetime.utcnow()
        return result

    def get_seo_info(self):
        """Lấy thông tin SEO (ưu tiên từ cache nếu chưa quá 1 giờ)"""
        if (self.seo_score is None or
                self.seo_last_checked is None or
                (datetime.utcnow() - self.seo_last_checked).total_seconds() > 3600):
            return self.update_seo_score()

        from app.admin.routes import calculate_blog_seo_score
        current_result = calculate_blog_seo_score(self)

        if current_result['score'] != self.seo_score:
            self.seo_score = current_result['score']
            self.seo_grade = current_result['grade']
            self.seo_last_checked = datetime.utcnow()
            db.session.commit()

        return current_result

    def __repr__(self):
        return f'<Blog {self.title}>'

    @property
    def created_at_vn(self):
        """Lấy created_at theo múi giờ Việt Nam"""
        from app.utils import utc_to_vn
        return utc_to_vn(self.created_at)

    @property
    def updated_at_vn(self):
        """Lấy updated_at theo múi giờ Việt Nam"""
        from app.utils import utc_to_vn
        return utc_to_vn(self.updated_at)


# ==================== FAQ MODEL ====================
class FAQ(db.Model):
    """Model câu hỏi thường gặp"""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FAQ {self.question[:50]}>'


# ==================== CONTACT MODEL ====================
class Contact(db.Model):
    """Model lưu thông tin liên hệ từ khách hàng"""
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name} - {self.email}>'

    @property
    def created_at_vn(self):
        """Lấy created_at theo múi giờ Việt Nam"""
        from app.utils import utc_to_vn
        return utc_to_vn(self.created_at)



# ==================== MEDIA MODEL ====================
class Media(db.Model):
    """Model quản lý hình ảnh/media files với SEO optimization"""
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    filepath = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    # SEO Fields
    alt_text = db.Column(db.String(255))
    title = db.Column(db.String(255))
    caption = db.Column(db.Text)

    # Organization
    album = db.Column(db.String(100))

    # ✅ THÊM 3 FIELD NÀY ĐỂ LƯU ĐIỂM SEO
    seo_score = db.Column(db.Integer, default=0)
    seo_grade = db.Column(db.String(5), default='F')
    seo_last_checked = db.Column(db.DateTime)

    # Metadata
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.filename}>'

    def get_url(self):
        return self.filepath if self.filepath.startswith('/') else f'/{self.filepath}'

    def get_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    # ✅ THAY THẾ 2 METHOD CŨ BẰNG 2 METHOD MỚI
    def update_seo_score(self):
        """Tính và lưu điểm SEO vào database"""
        from app.admin.routes import calculate_seo_score
        result = calculate_seo_score(self)
        self.seo_score = result['score']
        self.seo_grade = result['grade']
        self.seo_last_checked = datetime.utcnow()
        return result

    def get_seo_info(self):
        """Lấy thông tin SEO (ưu tiên từ cache)"""
        # Nếu chưa tính lần nào hoặc đã quá 1 giờ, tính lại
        if (self.seo_score is None or
                self.seo_last_checked is None or
                (datetime.utcnow() - self.seo_last_checked).total_seconds() > 3600):
            return self.update_seo_score()

        # Nếu có rồi, tính nhanh để so sánh
        from app.admin.routes import calculate_seo_score
        current_result = calculate_seo_score(self)

        # Nếu điểm thay đổi, update
        if current_result['score'] != self.seo_score:
            self.seo_score = current_result['score']
            self.seo_grade = current_result['grade']
            self.seo_last_checked = datetime.utcnow()
            db.session.commit()

        return current_result

# ==================== DỰ ÁN ====================
class Project(db.Model):
    """Model cho Dự án tiêu biểu"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    client = db.Column(db.String(200))  # Tên khách hàng
    location = db.Column(db.String(200))  # Địa điểm
    year = db.Column(db.Integer)  # Năm thực hiện

    description = db.Column(db.Text)  # Mô tả ngắn
    content = db.Column(db.Text)  # Nội dung chi tiết

    image = db.Column(db.String(300))  # Ảnh đại diện
    gallery = db.Column(db.Text)  # JSON array các ảnh gallery

    # Thông tin dự án
    project_type = db.Column(db.String(100))  # Loại dự án: Nhà ở, Văn phòng, Khách sạn...
    area = db.Column(db.String(100))  # Diện tích
    products_used = db.Column(db.Text)  # Sản phẩm đã sử dụng

    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Project {self.title}>'

    def get_gallery_images(self):
        """Parse gallery JSON"""
        if self.gallery:
            import json
            try:
                return json.loads(self.gallery)
            except:
                return []
        return []

# ==================== TUYỂN DỤNG ====================

class Job(db.Model):
    """Model cho Tuyển dụng"""
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)

    # Thông tin công việc
    department = db.Column(db.String(100))  # Phòng ban
    location = db.Column(db.String(200))  # Địa điểm làm việc
    job_type = db.Column(db.String(50))  # Full-time, Part-time, Contract
    level = db.Column(db.String(50))  # Junior, Senior, Manager...
    salary = db.Column(db.String(100))  # Mức lương
    experience = db.Column(db.String(100))  # Kinh nghiệm yêu cầu

    description = db.Column(db.Text)  # Mô tả công việc
    requirements = db.Column(db.Text)  # Yêu cầu (dạng HTML list)
    benefits = db.Column(db.Text)  # Quyền lợi (dạng HTML list)

    deadline = db.Column(db.DateTime)  # Hạn nộp hồ sơ
    contact_email = db.Column(db.String(200))  # Email nhận CV

    is_active = db.Column(db.Boolean, default=True)
    is_urgent = db.Column(db.Boolean, default=False)  # Tuyển gấp
    view_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Job {self.title}>'

    def is_expired(self):
        """Kiểm tra đã hết hạn chưa"""
        if self.deadline:
            return datetime.utcnow() > self.deadline
        return False

    @property
    def created_at_vn(self):
        from app.utils import utc_to_vn
        return utc_to_vn(self.created_at)

    @property
    def updated_at_vn(self):
        from app.utils import utc_to_vn
        return utc_to_vn(self.updated_at)

    @property
    def deadline_vn(self):
        from app.utils import utc_to_vn
        return utc_to_vn(self.deadline)

# ==================== HELPER FUNCTIONS ====================
def get_media_by_image_url(image_url):
    """
    Tìm Media record từ image URL (Cloudinary hoặc local)
    Hỗ trợ:
    - https://res.cloudinary.com/.../image.jpg
    - /static/uploads/image.jpg
    - uploads/image.jpg
    """
    if not image_url:
        return None

    # Case 1: Cloudinary URL - tìm theo filepath
    if image_url.startswith('http'):
        return Media.query.filter_by(filepath=image_url).first()

    # Case 2: Local path - chuẩn hóa và tìm theo filename
    # /static/uploads/products/abc.jpg → abc.jpg
    filename = image_url.split('/')[-1]

    # Tìm theo filename (có thể có nhiều file trùng tên)
    media = Media.query.filter_by(filename=filename).first()

    # Nếu không tìm thấy, thử tìm theo filepath
    if not media:
        # Chuẩn hóa path
        normalized_path = image_url
        if not normalized_path.startswith('/'):
            normalized_path = '/' + normalized_path
        if not normalized_path.startswith('/static/'):
            if normalized_path.startswith('/uploads/'):
                normalized_path = '/static' + normalized_path

        media = Media.query.filter_by(filepath=normalized_path).first()

    return media


# ==============================================================================
# THÊM ĐOẠN NÀY VÀO CUỐI FILE models.py (SAU CLASS Media)
# ==============================================================================

# ==================== HELPER FUNCTION ====================
def get_media_by_image_url(image_url):
    """
    Tìm Media record từ image URL (Cloudinary hoặc local)

    Hỗ trợ các format:
    - https://res.cloudinary.com/.../image.jpg (Cloudinary)
    - /static/uploads/products/image.jpg (Local)
    - uploads/products/image.jpg (Local không có /)

    Returns: Media object hoặc None
    """
    if not image_url:
        return None

    # Case 1: URL Cloudinary đầy đủ - tìm theo filepath
    if image_url.startswith('http://') or image_url.startswith('https://'):
        return Media.query.filter_by(filepath=image_url).first()

    # Case 2: Local path - tìm theo filename
    # Lấy tên file: /static/uploads/products/abc.jpg → abc.jpg
    filename = image_url.split('/')[-1]

    # Tìm theo filename (ưu tiên)
    media = Media.query.filter_by(filename=filename).first()

    if media:
        return media

    # Case 3: Nếu không tìm thấy, thử chuẩn hóa path và tìm lại
    normalized_path = image_url
    if not normalized_path.startswith('/'):
        normalized_path = '/' + normalized_path
    if not normalized_path.startswith('/static/'):
        if normalized_path.startswith('/uploads/'):
            normalized_path = '/static' + normalized_path
        else:
            normalized_path = '/static/' + normalized_path.lstrip('/')

    return Media.query.filter_by(filepath=normalized_path).first()


# ==================== CẬP NHẬT METHOD CHO PRODUCT ====================
def product_get_media_seo_info(self):
    """
    Lấy thông tin SEO từ Media Library dựa vào image path

    Priority:
    1. Tìm Media record theo image URL
    2. Fallback về thông tin legacy từ Product nếu không tìm thấy
    3. Fallback về tên Product nếu không có gì
    """
    if not self.image:
        return None

    # Tìm Media record
    media = get_media_by_image_url(self.image)

    if media:
        return {
            'alt_text': media.alt_text or self.name,
            'title': media.title or self.name,
            'caption': media.caption
        }

    # Fallback: dùng thông tin legacy từ Product (nếu có)
    return {
        'alt_text': self.image_alt_text or self.name,
        'title': self.image_title or self.name,
        'caption': self.image_caption
    }


# Gán lại method cho class Product
Product.get_media_seo_info = product_get_media_seo_info


# ==================== CẬP NHẬT METHOD CHO BANNER ====================
def banner_get_media_seo_info(self):
    """
    Lấy thông tin SEO từ Media Library cho Banner

    Priority:
    1. Media Library
    2. Fallback về title/subtitle của Banner
    """
    if not self.image:
        return None

    media = get_media_by_image_url(self.image)

    if media:
        return {
            'alt_text': media.alt_text or self.title,
            'title': media.title or self.title,
            'caption': media.caption or self.subtitle
        }

    # Fallback
    return {
        'alt_text': self.title,
        'title': self.title,
        'caption': self.subtitle
    }


# Gán lại method cho class Banner
Banner.get_media_seo_info = banner_get_media_seo_info


# ==================== CẬP NHẬT METHOD CHO BLOG ====================
def blog_get_media_seo_info(self):
    """
    Lấy thông tin SEO từ Media Library cho Blog

    Priority:
    1. Media Library
    2. Legacy fields từ Blog
    3. Fallback về title/excerpt
    """
    if not self.image:
        return None

    media = get_media_by_image_url(self.image)

    if media:
        return {
            'alt_text': media.alt_text or self.title,
            'title': media.title or self.title,
            'caption': media.caption or self.excerpt
        }

    # Fallback: dùng legacy fields
    return {
        'alt_text': self.image_alt_text or self.title,
        'title': self.image_title or self.title,
        'caption': self.image_caption or self.excerpt
    }


# Gán lại method cho class Blog
Blog.get_media_seo_info = blog_get_media_seo_info

# ==================== CẬP NHẬT METHOD CHO PROJECT ====================
def project_get_media_seo_info(self):
    """
    Lấy thông tin SEO từ Media Library cho Project

    Priority:
    1. Media Library
    2. Fallback về title/description của Project
    """
    if not self.image:
        return None

    media = get_media_by_image_url(self.image)

    if media:
        return {
            'alt_text': media.alt_text or self.title,
            'title': media.title or self.title,
            'caption': media.caption or self.description
        }

    # Fallback: dùng thông tin từ Project
    return {
        'alt_text': f"Dự án {self.title}" + (f" - {self.location}" if self.location else ""),
        'title': f"{self.title} ({self.year})" if self.year else self.title,
        'caption': self.description or f"Dự án {self.project_type} tại {self.location}"
    }


# Gán lại method cho class Project
Project.get_media_seo_info = project_get_media_seo_info

# ==============================================================================
# HẾT - ĐÃ CẬP NHẬT XONG
# ==============================================================================
class Settings(db.Model):
    """Model lưu cài đặt hệ thống (key-value)"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    group = db.Column(db.String(50), nullable=False)  # Nhóm: general, theme, seo, v.v.
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Settings {self.key}: {self.value}>'

# Helper function để get/set settings
def get_setting(key, default=None):
    """Lấy giá trị setting từ DB"""
    setting = Settings.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_setting(key, value, group='general', description=''):
    """Lưu hoặc cập nhật setting"""

    # ✅ BƯỚC 1: XỬ LÝ TUPLE TRƯỚC KHI GÁN (chỉ 1 lần duy nhất)
    if isinstance(value, tuple):
        if len(value) >= 1:
            value = str(value[0])  # Chỉ lấy URL từ tuple (filepath, metadata)
            # Optional: Lưu metadata vào description
            if len(value) > 1 and isinstance(value[1], dict):
                description += f" | Metadata: {value[1]}"
        else:
            value = str(value)

    # ✅ BƯỚC 2: ĐẢM BẢO VALUE LÀ STRING
    if not isinstance(value, str):
        value = str(value) if value is not None else ''

    # ✅ BƯỚC 3: TÌM HOẶC TẠO SETTING
    setting = Settings.query.filter_by(key=key).first()

    if setting:
        setting.value = value
        setting.group = group
        setting.description = description
    else:
        setting = Settings(key=key, value=value, group=group, description=description)
        db.session.add(setting)

    # ✅ BƯỚC 4: COMMIT
    db.session.commit()
    return setting