from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, PasswordField, SelectField, SubmitField, ColorField
from wtforms.fields import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError, InputRequired, NumberRange
from app.models import User, Category
from app.project_config import PROJECT_TYPE_CHOICES


# ==================== FORM ĐĂNG NHẬP ====================
class LoginForm(FlaskForm):
    """Form đăng nhập admin"""
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu')
    ])
    remember_me = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')


# ==================== FORM LIÊN HỆ ====================
class ContactForm(FlaskForm):
    """Form liên hệ từ khách hàng"""
    name = StringField('Họ và tên', validators=[
        DataRequired(message='Vui lòng nhập họ tên'),
        Length(min=2, max=100, message='Họ tên từ 2-100 ký tự')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    phone = StringField('Số điện thoại', validators=[
        Optional(),
        Length(max=20)
    ])
    subject = StringField('Tiêu đề', validators=[
        Optional(),
        Length(max=200)
    ])
    message = TextAreaField('Nội dung', validators=[
        DataRequired(message='Vui lòng nhập nội dung'),
        Length(min=10, message='Nội dung tối thiểu 10 ký tự')
    ])
    submit = SubmitField('Gửi liên hệ')


# ==================== FORM DANH MỤC ====================
class CategoryForm(FlaskForm):
    """Form quản lý danh mục"""
    name = StringField('Tên danh mục', validators=[
        DataRequired(message='Vui lòng nhập tên danh mục'),
        Length(min=2, max=100)
    ])
    slug = StringField('Slug (URL)', validators=[
        DataRequired(message='Vui lòng nhập slug'),
        Length(min=2, max=100)
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    image = FileField('Hình ảnh', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Chỉ chấp nhận ảnh!')
    ])
    is_active = BooleanField('Kích hoạt')
    submit = SubmitField('Lưu danh mục')


# ==================== FORM SẢN PHẨM ====================
class ProductForm(FlaskForm):
    """Form quản lý sản phẩm"""
    name = StringField('Tên sản phẩm', validators=[
        DataRequired(message='Vui lòng nhập tên sản phẩm'),
        Length(min=2, max=200)
    ])
    slug = StringField('Slug (URL)', validators=[
        DataRequired(message='Vui lòng nhập slug'),
        Length(min=2, max=200)
    ])
    description = TextAreaField('Mô tả sản phẩm', validators=[Optional()])
    price = FloatField('Giá bán', validators=[
        InputRequired(message='Vui lòng nhập giá'),
        NumberRange(min=0, message='Giá phải >= 0')
    ])
    old_price = FloatField('Giá cũ', validators=[Optional(), NumberRange(min=0)])
    category_id = SelectField('Danh mục', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn danh mục')
    ])
    image = FileField('Hình ảnh chính', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Chỉ chấp nhận ảnh!')
    ])
    is_featured = BooleanField('Sản phẩm nổi bật')
    is_active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Lưu sản phẩm')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Load danh mục vào dropdown
        self.category_id.choices = [(0, '-- Chọn danh mục --')] + [
            (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()
        ]


# ==================== FORM BANNER ====================
class BannerForm(FlaskForm):
    """Form quản lý banner slider"""
    title = StringField('Tiêu đề', validators=[
        Optional(),
        Length(max=200)
    ])
    subtitle = StringField('Phụ đề', validators=[
        Optional(),
        Length(max=255)
    ])
    image = FileField('Hình ảnh', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Chỉ chấp nhận ảnh!')
    ])
    link = StringField('Link', validators=[Optional(), Length(max=255)])
    button_text = StringField('Text nút', validators=[Optional(), Length(max=50)])
    order = FloatField('Thứ tự', validators=[Optional()])
    is_active = BooleanField('Kích hoạt')
    submit = SubmitField('Lưu banner')


# ==================== FORM BLOG ====================
class BlogForm(FlaskForm):
    """Form quản lý tin tức/blog với SEO optimization"""

    # Basic fields
    title = StringField('Tiêu đề', validators=[
        DataRequired(message='Vui lòng nhập tiêu đề'),
        Length(min=5, max=200)
    ])
    slug = StringField('Slug (URL)', validators=[
        DataRequired(message='Vui lòng nhập slug'),
        Length(min=5, max=200)
    ])
    excerpt = TextAreaField('Mô tả ngắn', validators=[Optional()])
    content = TextAreaField('Nội dung', validators=[
        DataRequired(message='Vui lòng nhập nội dung')
    ])
    image = FileField('Hình ảnh', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Chỉ chấp nhận ảnh!')
    ])
    author = StringField('Tác giả', validators=[Optional(), Length(max=100)])
    is_featured = BooleanField('Tin nổi bật')
    is_active = BooleanField('Kích hoạt')

    # ✅ THÊM SEO FIELDS
    focus_keyword = StringField('Focus Keyword', validators=[
        Optional(),
        Length(max=100, message='Focus Keyword tối đa 100 ký tự')
    ])
    meta_title = StringField('Meta Title (SEO Title)', validators=[
        Optional(),
        Length(max=70, message='Meta Title nên <= 60 ký tự để hiển thị đầy đủ trên Google')
    ])
    meta_description = TextAreaField('Meta Description', validators=[
        Optional(),
        Length(max=160, message='Meta Description nên 120-160 ký tự')
    ])
    meta_keywords = StringField('Meta Keywords (optional)', validators=[
        Optional(),
        Length(max=255)
    ])

    submit = SubmitField('Lưu bài viết')

# ==================== FORM FAQ ====================
class FAQForm(FlaskForm):
    """Form quản lý câu hỏi thường gặp"""
    question = StringField('Câu hỏi', validators=[
        DataRequired(message='Vui lòng nhập câu hỏi'),
        Length(min=5, max=255)
    ])
    answer = TextAreaField('Câu trả lời', validators=[
        DataRequired(message='Vui lòng nhập câu trả lời')
    ])
    order = FloatField('Thứ tự', validators=[Optional()])
    is_active = BooleanField('Kích hoạt')
    submit = SubmitField('Lưu FAQ')


# ==================== FORM USER ====================
class UserForm(FlaskForm):
    """Form quản lý người dùng với RBAC"""
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập'),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    password = PasswordField('Mật khẩu', validators=[
        Optional(),
        Length(min=6, message='Mật khẩu tối thiểu 6 ký tự')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        EqualTo('password', message='Mật khẩu không khớp')
    ])

    # ✅ THAY ĐỔI: Thay is_admin → role_id
    role_id = SelectField('Vai trò', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn vai trò')
    ])

    # ✅ GIỮ LẠI: is_admin checkbox (hidden, chỉ dùng khi cần tương thích)
    # Có thể bỏ sau khi migrate xong

    submit = SubmitField('Lưu người dùng')

    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user

        # ✅ Load danh sách roles vào dropdown
        from app.models_rbac import Role
        roles = Role.query.filter_by(is_active=True).order_by(Role.priority.desc()).all()
        self.role_id.choices = [(r.id, r.display_name) for r in roles]

    def validate_username(self, username):
        """Kiểm tra username có trùng không"""
        user = User.query.filter_by(username=username.data).first()
        if user and (self.user is None or user.id != self.user.id):
            raise ValidationError('Tên đăng nhập đã tồn tại')

    def validate_email(self, email):
        """Kiểm tra email có trùng không"""
        user = User.query.filter_by(email=email.data).first()
        if user and (self.user is None or user.id != self.user.id):
            raise ValidationError('Email đã tồn tại')


# ==================== THÊM MỚI: RoleForm ====================
class RoleForm(FlaskForm):
    """Form quản lý Role"""
    name = StringField('Tên role (code)', validators=[
        DataRequired(message='Vui lòng nhập tên role'),
        Length(min=3, max=50)
    ])
    display_name = StringField('Tên hiển thị', validators=[
        DataRequired(message='Vui lòng nhập tên hiển thị'),
        Length(min=3, max=100)
    ])
    description = StringField('Mô tả', validators=[Optional()])
    priority = SelectField('Độ ưu tiên', coerce=int, choices=[
        (100, 'Cao nhất (100)'),
        (70, 'Cao (70)'),
        (50, 'Trung bình (50)'),
        (30, 'Thấp (30)'),
        (10, 'Thấp nhất (10)')
    ])
    color = SelectField('Màu badge', choices=[
        ('danger', 'Đỏ (Admin)'),
        ('primary', 'Xanh dương (Editor)'),
        ('info', 'Xanh nhạt (Moderator)'),
        ('success', 'Xanh lá'),
        ('warning', 'Vàng'),
        ('secondary', 'Xám (User)')
    ])
    is_active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Lưu vai trò')


# ==================== THÊM MỚI: PermissionForm ====================
class PermissionForm(FlaskForm):
    """Form quản lý Permission"""
    name = StringField('Tên permission (code)', validators=[
        DataRequired(message='Vui lòng nhập tên permission'),
        Length(min=3, max=100)
    ])
    display_name = StringField('Tên hiển thị', validators=[
        DataRequired(message='Vui lòng nhập tên hiển thị'),
        Length(min=3, max=100)
    ])
    description = StringField('Mô tả', validators=[Optional()])
    category = SelectField('Danh mục', choices=[
        ('products', 'Sản phẩm'),
        ('blogs', 'Blog'),
        ('media', 'Media'),
        ('users', 'Người dùng'),
        ('contacts', 'Liên hệ'),
        ('projects', 'Dự án'),
        ('jobs', 'Tuyển dụng'),
        ('system', 'Hệ thống'),
    ])
    icon = StringField('Icon (Bootstrap)', validators=[
        Optional(),
        Length(max=50)
    ])
    is_active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Lưu quyền')


# ==================== FORM SEO MEDIA ====================

class MediaSEOForm(FlaskForm):
    """Form chỉnh sửa SEO cho media (không upload file mới)"""
    alt_text = StringField('Alt Text', validators=[
        DataRequired(message='Alt Text là bắt buộc cho SEO'),
        Length(min=10, max=125, message='Alt Text nên từ 30-125 ký tự')
    ])
    title = StringField('Title', validators=[
        Optional(),
        Length(max=255)
    ])
    caption = TextAreaField('Caption', validators=[
        Optional(),
        Length(max=500)
    ])
    album = StringField('Album', validators=[Optional()])
    submit = SubmitField('Lưu thay đổi')


# ==================== QUẢN LÝ DỰ ÁN ====================
class ProjectForm(FlaskForm):
    """Form cho Dự án tiêu biểu"""
    title = StringField('Tên dự án *', validators=[DataRequired()])
    slug = StringField('Slug (URL)', validators=[DataRequired()])
    client = StringField('Khách hàng')
    location = StringField('Địa điểm')
    year = IntegerField('Năm thực hiện', validators=[Optional()])

    description = TextAreaField('Mô tả ngắn')
    content = TextAreaField('Nội dung chi tiết')

    image = FileField('Ảnh đại diện', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Chỉ chấp nhận file ảnh!')
    ])

    project_type = SelectField(
        'Loại dự án',
        choices=PROJECT_TYPE_CHOICES,
        validators=[DataRequired()]
    )

    area = StringField('Diện tích')
    products_used = TextAreaField('Sản phẩm sử dụng')

    is_featured = BooleanField('Dự án nổi bật')
    is_active = BooleanField('Kích hoạt', default=True)

    submit = SubmitField('Lưu dự án')

# ==================== QUẢN LÍ TUYỂN DỤNG ====================
class JobForm(FlaskForm):
    """Form cho Tuyển dụng"""
    title = StringField('Vị trí tuyển dụng *', validators=[DataRequired()])
    slug = StringField('Slug (URL)', validators=[DataRequired()])

    department = StringField('Phòng ban')
    location = StringField('Địa điểm làm việc *', validators=[DataRequired()])

    job_type = SelectField('Hình thức', choices=[
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Hợp đồng'),
        ('internship', 'Thực tập')
    ])

    level = SelectField('Cấp bậc', choices=[
        ('intern', 'Thực tập sinh'),
        ('Fresher', 'Mới ra trường'),
        ('junior', 'Junior'),
        ('middle', 'Middle'),
        ('senior', 'Senior'),
        ('lead', 'Team Lead'),
        ('manager', 'Manager')
    ])

    salary = StringField('Mức lương', validators=[DataRequired()])
    experience = StringField('Kinh nghiệm yêu cầu')

    description = TextAreaField('Mô tả công việc', validators=[DataRequired()])
    requirements = TextAreaField('Yêu cầu ứng viên')
    benefits = TextAreaField('Quyền lợi')

    deadline = DateField('Hạn nộp hồ sơ', validators=[Optional()])
    contact_email = StringField('Email nhận CV', validators=[DataRequired(), Email()])

    is_active = BooleanField('Đang tuyển', default=True)
    is_urgent = BooleanField('Tuyển gấp')

    submit = SubmitField('Lưu tin tuyển dụng')


class SettingsForm(FlaskForm):
    """Form quản lý cài đặt hệ thống, chia nhóm"""

    # General Settings
    website_name = StringField('Tên website', validators=[DataRequired()])
    slogan = StringField('Slogan', validators=[Optional()])
    address = StringField('Địa chỉ', validators=[Optional()])
    email = StringField('Email chính', validators=[Email()])
    hotline = StringField('Hotline', validators=[Optional()])
    main_url = StringField('URL chính', validators=[Optional()])
    company_info = TextAreaField('Thông tin công ty', validators=[Optional()])


    # Theme/UI Settings
    logo = FileField('Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    logo_chatbot = FileField('Logo chatbot', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    primary_color = ColorField('Màu chủ đạo', validators=[Optional()])

    # SEO & Meta Defaults
    meta_title = StringField('Meta Title mặc định', validators=[DataRequired()])
    meta_description = TextAreaField('Meta Description mặc định', validators=[DataRequired()])
    meta_keywords = StringField('Meta Keywords', validators=[Optional()])

    # ✅ THÊM CÁC TRƯỜNG FAVICON MỚI
    favicon_ico = FileField('Favicon (.ico)', validators=[FileAllowed(['ico'])])
    favicon_png = FileField('Favicon PNG (96x96)', validators=[FileAllowed(['png'])])
    favicon_svg = FileField('Favicon SVG', validators=[FileAllowed(['svg'])])
    apple_touch_icon = FileField('Apple Touch Icon (180x180)', validators=[FileAllowed(['png'])])


    index_meta_description = TextAreaField('Meta Description Trang Chủ', validators=[Length(max=160)])
    about_meta_description = TextAreaField('Meta Description Giới Thiệu', validators=[Length(max=160)])
    contact_meta_description = TextAreaField('Meta Description Liên Hệ', validators=[Length(max=160)])
    products_meta_description = TextAreaField('Meta Description Sản Phẩm', validators=[Length(max=160)])
    blog_meta_description = TextAreaField('Meta Description Blog', validators=[Length(max=160)])
    careers_meta_description = TextAreaField('Meta Description Tuyển Dụng', validators=[Length(max=160)])
    faq_meta_description = TextAreaField('Meta Description FAQ', validators=[Length(max=160)])
    projects_meta_description = TextAreaField('Meta Description Dự Án', validators=[Length(max=160)])
    product_meta_description = TextAreaField('Meta Description Chi Tiết Sản Phẩm', validators=[Length(max=160)])
    favicon = FileField('Favicon', validators=[FileAllowed(['ico', 'png'])])
    default_share_image = FileField('Ảnh chia sẻ mặc định', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])

    # Contact & Social Settings
    contact_email = StringField('Email liên hệ', validators=[Email()])
    facebook_url = StringField('Facebook', validators=[Optional()])
    zalo_url = StringField('Zalo', validators=[Optional()])
    tiktok_url = StringField('TikTok', validators=[Optional()])
    youtube_url = StringField('YouTube', validators=[Optional()])
    google_maps = TextAreaField('Bản đồ Google Maps (embed code)', validators=[Optional()])
    hotline_north = StringField('Hotline Miền Bắc', validators=[Optional()])
    hotline_central = StringField('Hotline Miền Trung', validators=[Optional()])
    hotline_south = StringField('Hotline Miền Nam', validators=[Optional()])
    working_hours = StringField('Giờ làm việc', validators=[Optional()])
    facebook_messenger_url = StringField('Facebook Messenger', validators=[Optional()])

    branch_addresses = TextAreaField('Danh sách chi nhánh', validators=[Optional()])

    # System & Security Settings
    login_attempt_limit = IntegerField('Giới hạn đăng nhập sai', validators=[NumberRange(min=3, max=10)])
    cache_time = IntegerField('Thời gian cache dữ liệu (giây)', validators=[NumberRange(min=0)])

    # Integration Settings
    cloudinary_api_key = StringField('API Key Cloudinary', validators=[Optional()])
    gemini_api_key = StringField('API Key Gemini/OpenAI', validators=[Optional()])
    google_analytics = StringField('Google Analytics ID', validators=[Optional()])
    shopee_api = StringField('Shopee Integration', validators=[Optional()])
    tiktok_api = StringField('TikTok Integration', validators=[Optional()])
    zalo_oa = StringField('Zalo OA', validators=[Optional()])

    # Content Defaults
    terms_of_service = TextAreaField('Điều khoản dịch vụ', validators=[Optional()])
    shipping_policy = TextAreaField('Chính sách vận chuyển', validators=[Optional()])
    return_policy = TextAreaField('Chính sách đổi trả', validators=[Optional()])
    warranty_policy = TextAreaField('Chính sách bảo hành', validators=[Optional()])
    privacy_policy = TextAreaField('Chính sách bảo mật', validators=[Optional()])

    contact_form = TextAreaField('Form liên hệ mặc định', validators=[Optional()])
    default_posts_per_page = IntegerField('Số lượng bài viết mặc định', validators=[NumberRange(min=1, max=50)])

    logo_url = None
    logo_chatbot_url = None
    favicon_url = None
    default_share_image_url = None
    favicon_ico_url = None
    favicon_png_url = None
    favicon_svg_url = None
    apple_touch_icon_url = None


    submit = SubmitField('Lưu cài đặt')