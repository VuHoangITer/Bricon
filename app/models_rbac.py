from app import db
from datetime import datetime

# ==================== BẢNG TRUNG GIAN ====================
role_permissions = db.Table('role_permissions',
                            db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                            db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
                            db.Column('created_at', db.DateTime, default=datetime.utcnow)
                            )


# ==================== ROLE MODEL ====================
class Role(db.Model):
    """Model cho vai trò (Admin, Editor, Moderator, User)"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, default=0)  # Cao = quyền lớn
    color = db.Column(db.String(20), default='secondary')  # Bootstrap colors
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='role_obj', lazy='dynamic')
    permissions = db.relationship('Permission',
                                  secondary=role_permissions,
                                  backref=db.backref('roles', lazy='dynamic'),
                                  lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    def has_permission(self, permission_name):
        """Kiểm tra role có permission cụ thể không"""
        return self.permissions.filter_by(name=permission_name, is_active=True).first() is not None

    def add_permission(self, permission):
        """Thêm permission vào role"""
        if not self.has_permission(permission.name):
            self.permissions.append(permission)

    def remove_permission(self, permission):
        """Xóa permission khỏi role"""
        if self.has_permission(permission.name):
            self.permissions.remove(permission)

    def get_permissions_by_category(self):
        """Lấy permissions nhóm theo category"""
        perms = self.permissions.filter_by(is_active=True).order_by(Permission.category, Permission.name).all()
        grouped = {}
        for perm in perms:
            cat = perm.category or 'other'
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(perm)
        return grouped

    @property
    def user_count(self):
        """Đếm số user có role này"""
        return self.users.filter_by(is_active=True).count()


# ==================== PERMISSION MODEL ====================
class Permission(db.Model):
    """Model cho quyền hạn chi tiết"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    icon = db.Column(db.String(50), default='bi-key')  # Bootstrap icon
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Permission {self.name}>'

    @property
    def role_count(self):
        """Đếm số role có permission này"""
        return self.roles.count()


# ==================== HELPER FUNCTIONS ====================
def init_default_roles():
    """Khởi tạo roles mặc định (gọi trong seed script)"""
    roles_data = [
        {
            'name': 'admin',
            'display_name': 'Quản trị viên',
            'description': 'Toàn quyền quản lý hệ thống',
            'priority': 100,
            'color': 'danger'
        },
        {
            'name': 'editor',
            'display_name': 'Biên tập viên',
            'description': 'Quản lý nội dung: blog, sản phẩm, media',
            'priority': 70,
            'color': 'primary'
        },
        {
            'name': 'moderator',
            'display_name': 'Kiểm duyệt viên',
            'description': 'Kiểm duyệt blog, xử lý liên hệ',
            'priority': 50,
            'color': 'info'
        },
        {
            'name': 'user',
            'display_name': 'Người dùng',
            'description': 'Chỉ xem thông tin cơ bản',
            'priority': 10,
            'color': 'secondary'
        }
    ]

    for data in roles_data:
        role = Role.query.filter_by(name=data['name']).first()
        if not role:
            role = Role(**data)
            db.session.add(role)
            print(f"✓ Created role: {data['name']}")

    db.session.commit()


def init_default_permissions():
    """Khởi tạo permissions mặc định"""
    permissions_data = [
        # ===== PRODUCTS =====
        ('view_products', 'Xem sản phẩm', 'products', 'bi-box-seam'),
        ('manage_products', 'Quản lý sản phẩm', 'products', 'bi-box-seam'),
        ('manage_categories', 'Quản lý danh mục', 'products', 'bi-tag'),

        # ===== BLOGS =====
        ('view_blogs', 'Xem blog', 'blogs', 'bi-newspaper'),
        ('create_blog', 'Tạo blog', 'blogs', 'bi-plus-circle'),
        ('edit_own_blog', 'Sửa blog của mình', 'blogs', 'bi-pencil'),
        ('edit_all_blogs', 'Sửa tất cả blog', 'blogs', 'bi-pencil-square'),
        ('delete_blog', 'Xóa blog', 'blogs', 'bi-trash'),
        ('publish_blog', 'Xuất bản blog', 'blogs', 'bi-check-circle'),

        # ===== MEDIA =====
        ('view_media', 'Xem thư viện media', 'media', 'bi-folder2-open'),
        ('upload_media', 'Upload media', 'media', 'bi-cloud-upload'),
        ('edit_media', 'Chỉnh sửa media', 'media', 'bi-pencil'),
        ('delete_media', 'Xóa media', 'media', 'bi-trash'),
        ('manage_albums', 'Quản lý albums', 'media', 'bi-collection'),

        # ===== USERS =====
        ('view_users', 'Xem danh sách user', 'users', 'bi-people'),
        ('manage_users', 'Quản lý users', 'users', 'bi-person-gear'),
        ('assign_roles', 'Phân quyền user', 'users', 'bi-shield-check'),

        # ===== CONTACTS =====
        ('view_contacts', 'Xem liên hệ', 'contacts', 'bi-envelope'),
        ('manage_contacts', 'Quản lý liên hệ', 'contacts', 'bi-envelope-check'),

        # ===== PROJECTS =====
        ('view_projects', 'Xem dự án', 'projects', 'bi-building'),
        ('manage_projects', 'Quản lý dự án', 'projects', 'bi-building-gear'),

        # ===== JOBS =====
        ('view_jobs', 'Xem tuyển dụng', 'jobs', 'bi-briefcase'),
        ('manage_jobs', 'Quản lý tuyển dụng', 'jobs', 'bi-briefcase-fill'),

        # ===== SYSTEM =====
        ('manage_banners', 'Quản lý banners', 'system', 'bi-images'),
        ('manage_faqs', 'Quản lý FAQs', 'system', 'bi-question-circle'),
        ('view_dashboard', 'Xem dashboard', 'system', 'bi-speedometer2'),
        ('manage_settings', 'Quản lý cài đặt hệ thống', 'system', 'bi-gear'),
        ('manage_roles', 'Quản lý phân quyền', 'system', 'bi-shield-lock'),

        # ===== QUIZ (THÊM MỚI) =====
        ('view_quiz', 'Xem quiz', 'quiz', 'bi-card-checklist'),
        ('manage_quiz', 'Quản lý quiz', 'quiz', 'bi-card-list'),
    ]

    for name, display_name, category, icon in permissions_data:
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            perm = Permission(
                name=name,
                display_name=display_name,
                category=category,
                icon=icon
            )
            db.session.add(perm)
            print(f"✓ Created permission: {name}")

    db.session.commit()


def assign_default_permissions():
    """Gán permissions cho các roles"""
    # 1. ADMIN - Toàn quyền
    admin = Role.query.filter_by(name='admin').first()
    if admin:
        all_perms = Permission.query.filter_by(is_active=True).all()
        for perm in all_perms:
            admin.add_permission(perm)
        print("✓ Assigned all permissions to Admin")

    # 2. EDITOR
    editor = Role.query.filter_by(name='editor').first()
    if editor:
        editor_perms = [
            'view_dashboard',
            'view_products', 'manage_products', 'manage_categories',
            'view_blogs', 'create_blog', 'edit_all_blogs', 'delete_blog', 'publish_blog',
            'view_media', 'upload_media', 'edit_media', 'manage_albums',
            'view_projects', 'manage_projects',
            'view_contacts',
            'manage_faqs', 'manage_banners'
        ]
        for perm_name in editor_perms:
            perm = Permission.query.filter_by(name=perm_name).first()
            if perm:
                editor.add_permission(perm)
        print("✓ Assigned permissions to Editor")

    # 3. MODERATOR
    moderator = Role.query.filter_by(name='moderator').first()
    if moderator:
        mod_perms = [
            'view_dashboard',
            'view_products',
            'view_blogs', 'create_blog', 'edit_own_blog',
            'view_media', 'upload_media',
            'view_contacts', 'manage_contacts',
            'view_projects'
        ]
        for perm_name in mod_perms:
            perm = Permission.query.filter_by(name=perm_name).first()
            if perm:
                moderator.add_permission(perm)
        print("✓ Assigned permissions to Moderator")

    # 4. USER
    user = Role.query.filter_by(name='user').first()
    if user:
        user_perms = ['view_dashboard']
        for perm_name in user_perms:
            perm = Permission.query.filter_by(name=perm_name).first()
            if perm:
                user.add_permission(perm)
        print("✓ Assigned permissions to User")

    db.session.commit()