from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app, abort
from app import db
from app.models import Product, Category, Banner, Blog, FAQ, Contact, Project, Job, get_setting
from app.forms import ContactForm
from sqlalchemy import or_
from app.project_config import PROJECT_TYPES
from jinja2 import Template
from sqlalchemy.orm import joinedload, load_only
import os

# Tạo Blueprint cho frontend
main_bp = Blueprint('main', __name__)


# ==================== TRANG CHỦ ====================
@main_bp.route('/')
def index():
    """Trang chủ"""
    # Lấy banners đang active
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.order).all()

    # Lấy sản phẩm nổi bật (featured)
    featured_products = Product.query.filter_by(
        is_featured=True,
        is_active=True
    ).limit(3).all()

    # Lấy sản phẩm mới nhất
    latest_products = Product.query.filter_by(
        is_active=True
    ).order_by(Product.created_at.desc()).limit(3).all()

    # Lấy tin tức nổi bật
    featured_blogs = (Blog.query
                      .options(load_only(Blog.slug, Blog.title, Blog.created_at, Blog.image))
                      .filter_by(is_featured=True, is_active=True)
                      ).limit(3).all()

    featured_projects = Project.query.filter_by(is_featured=True, is_active=True).order_by(
        Project.created_at.desc()).limit(6).all()

    return render_template('index.html',
                           banners=banners,
                           featured_products=featured_products,
                           latest_products=latest_products,
                           featured_blogs=featured_blogs,
                           featured_projects=featured_projects)


# ==================== GIỚI THIỆU ====================
@main_bp.route('/gioi-thieu')
def about():
    """Trang giới thiệu"""
    return render_template('about.html')


# ==================== SẢN PHẨM ====================
@main_bp.route('/san-pham')
@main_bp.route('/loai-san-pham/<category_slug>')
def products(category_slug=None):
    """Trang danh sách sản phẩm với filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'latest')

    # Xử lý backward compatibility cho URL cũ
    old_category_id = request.args.get('category', type=int)
    if old_category_id:
        category = Category.query.get(old_category_id)
        if category and category.is_active:
            # Redirect 301 (permanent) đến URL mới với slug
            return redirect(url_for('main.products',
                                    category_slug=category.slug,
                                    search=search if search else None,
                                    sort=sort if sort != 'latest' else None,
                                    page=page if page > 1 else None),
                            code=301)
        elif not category:
            # Category không tồn tại, chuyển về trang products chung
            flash('Danh mục không tồn tại.', 'warning')
            return redirect(url_for('main.products'))

    # Redirect URL cũ /products sang /san-pham
    if request.path == '/products' or request.path.startswith('/products/category/'):
        # Lấy category_slug từ path cũ nếu có
        old_path_parts = request.path.split('/')
        if len(old_path_parts) > 3 and old_path_parts[2] == 'category':
            old_slug = old_path_parts[3]
            return redirect(url_for('main.products',
                                    category_slug=old_slug,
                                    search=search if search else None,
                                    sort=sort if sort != 'latest' else None,
                                    page=page if page > 1 else None),
                            code=301)
        else:
            return redirect(url_for('main.products',
                                    search=search if search else None,
                                    sort=sort if sort != 'latest' else None,
                                    page=page if page > 1 else None),
                            code=301)

    # Query cơ bản
    query = Product.query.options(joinedload(Product.category)).filter_by(is_active=True)
    current_category = None

    # Filter theo danh mục slug
    if category_slug:
        current_category = Category.query.filter_by(
            slug=category_slug,
            is_active=True
        ).first_or_404()
        query = query.filter_by(category_id=current_category.id)

    # Search theo tên
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    # Sắp xếp
    if sort == 'latest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.views.desc())

    # Phân trang
    per_page = int(get_setting('default_posts_per_page', '12'))

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    products = pagination.items
    categories = Category.query.filter_by(is_active=True).all()

    return render_template('products.html',
                           products=products,
                           categories=categories,
                           pagination=pagination,
                           current_category=current_category,
                           current_search=search,
                           current_sort=sort)


from datetime import datetime, timedelta


@main_bp.route('/san-pham/<slug>')
def product_detail(slug):
    """Trang chi tiết sản phẩm với render động meta description"""
    product = Product.query.options(joinedload(Product.category)) \
        .filter_by(slug=slug, is_active=True).first_or_404()

    # Tăng lượt xem
    product.views += 1
    db.session.commit()

    # Lấy sản phẩm liên quan (cùng danh mục)
    related_products = Product.query.options(joinedload(Product.category)) \
        .filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()

    # ✅ XỬ LÝ META DESCRIPTION ĐỘNG
    rendered_meta_description = None

    # Lấy template từ settings
    meta_template = get_setting('product_meta_description', '')

    if meta_template and ('{{' in meta_template or '{%' in meta_template):
        try:
            # Render template với context đầy đủ
            template = Template(meta_template)
            rendered_meta_description = template.render(
                product=product,
                get_setting=get_setting
            )
        except Exception as e:
            # Fallback: Simple string replace nếu template lỗi
            print(f"⚠️ Lỗi render meta template: {e}")
            rendered_meta_description = meta_template.replace('{{ product.name }}', product.name or '')
            rendered_meta_description = rendered_meta_description.replace(
                '{{ get_setting(\'website_name\', \'BRICON VIỆT NAM\') }}',
                get_setting('website_name', 'BRICON VIỆT NAM'))
    elif meta_template:
        # Template không có biến động
        rendered_meta_description = meta_template
    else:
        # Fallback mặc định nếu không có template
        rendered_meta_description = f"Mua {product.name} chất lượng cao từ {get_setting('website_name', 'BRICON VIỆT NAM')} với giá tốt nhất."

    return render_template('product_detail.html',
                           product=product,
                           related_products=related_products,
                           rendered_meta_description=rendered_meta_description,
                           now=datetime.now(),
                           timedelta=timedelta)


# Route cũ redirect sang mới
@main_bp.route('/product/<slug>')
def old_product_detail(slug):
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.product_detail', slug=slug), code=301)


# ==================== TIN TỨC / BLOG ====================
@main_bp.route('/tin-tuc')
def blog():
    """Trang danh sách blog"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    # Query
    query = (Blog.query
             .options(
        joinedload(Blog.author_obj),
        load_only(
            Blog.id, Blog.slug, Blog.title, Blog.excerpt, Blog.image,
            Blog.created_at, Blog.updated_at, Blog.views, Blog.author, Blog.is_featured
        )
    )
             .filter_by(is_active=True)
             )

    # Search
    if search:
        query = query.filter(
            or_(
                Blog.title.ilike(f'%{search}%'),
                Blog.excerpt.ilike(f'%{search}%')
            )
        )

    # Sắp xếp mới nhất
    query = query.order_by(Blog.created_at.desc())

    # Phân trang
    per_page = int(get_setting('default_posts_per_page', '9'))

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    blogs = pagination.items

    # Bài viết nổi bật sidebar
    featured_blogs = (Blog.query
                      .options(load_only(Blog.slug, Blog.title, Blog.created_at, Blog.views, Blog.image))
                      .filter_by(is_featured=True, is_active=True)
                      ).limit(5).all()

    return render_template('blog.html',
                           blogs=blogs,
                           pagination=pagination,
                           featured_blogs=featured_blogs,
                           current_search=search)


@main_bp.route('/tin-tuc/<slug>')
def blog_detail(slug):
    """Trang chi tiết blog"""
    blog = (Blog.query
            .options(joinedload(Blog.author_obj))
            .filter_by(slug=slug, is_active=True)
            ).first_or_404()

    # Tăng lượt xem
    blog.views += 1
    db.session.commit()

    # Bài viết liên quan
    related_blogs = (Blog.query
                     .options(load_only(Blog.slug, Blog.title, Blog.created_at, Blog.image))
                     .filter(Blog.id != blog.id, Blog.is_active == True)
                     .order_by(Blog.created_at.desc())
                     ).limit(3).all()

    return render_template('blog_detail.html',
                           blog=blog,
                           related_blogs=related_blogs)


# Route cũ redirect sang mới
@main_bp.route('/blog')
def old_blog():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.blog'), code=301)


@main_bp.route('/blog/<slug>')
def old_blog_detail(slug):
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.blog_detail', slug=slug), code=301)


# ==================== LIÊN HỆ ====================
@main_bp.route('/lien-he', methods=['GET', 'POST'])
def contact():
    """Trang liên hệ"""
    form = ContactForm()

    if form.validate_on_submit():
        # Tạo contact mới
        contact = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data
        )

        db.session.add(contact)
        db.session.commit()

        flash('Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất.', 'success')
        return redirect(url_for('main.contact'))

    return render_template('contact.html', form=form)


# Route cũ redirect sang mới
@main_bp.route('/contact', methods=['GET', 'POST'])
def old_contact():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.contact'), code=301)


# ==================== CHÍNH SÁCH ====================
@main_bp.route('/chinh-sach')
def policy():
    """Trang chính sách"""
    return render_template('policy.html')


# Route cũ redirect sang mới
@main_bp.route('/policy')
def old_policy():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.policy'), code=301)


# ==================== FAQ ====================
@main_bp.route('/cau-hoi-thuong-gap')
def faq():
    """Trang câu hỏi thường gặp"""
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.order).all()
    return render_template('faq.html', faqs=faqs)


# Route cũ redirect sang mới
@main_bp.route('/faq')
def old_faq():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.faq'), code=301)


# ==================== SEARCH ====================
@main_bp.route('/tim-kiem')
def search():
    """Trang tìm kiếm tổng hợp"""
    keyword = request.args.get('q', '')

    if not keyword:
        return redirect(url_for('main.index'))

    # Tìm sản phẩm
    products = Product.query.filter(
        Product.name.ilike(f'%{keyword}%'),
        Product.is_active == True
    ).limit(10).all()

    # Tìm blog
    blogs = Blog.query.filter(
        or_(
            Blog.title.ilike(f'%{keyword}%'),
            Blog.excerpt.ilike(f'%{keyword}%')
        ),
        Blog.is_active == True
    ).limit(5).all()

    return render_template('search.html',
                           keyword=keyword,
                           products=products,
                           blogs=blogs)


# Route cũ redirect sang mới
@main_bp.route('/search')
def old_search():
    """Redirect URL cũ sang URL mới"""
    keyword = request.args.get('q', '')
    return redirect(url_for('main.search', q=keyword), code=301)


# ==================== DỰ ÁN ====================
@main_bp.route('/du-an')
def projects():
    """Trang danh sách dự án"""
    page = request.args.get('page', 1, type=int)
    project_type = request.args.get('type', '')

    query = (Project.query
             .options(
        load_only(
            Project.id, Project.slug, Project.title, Project.image,
            Project.description, Project.location, Project.year,
            Project.project_type, Project.is_featured
        )
    )
             .filter_by(is_active=True)
             )

    if project_type:
        query = query.filter_by(project_type=project_type)

    projects = query.order_by(Project.year.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    featured_projects = (Project.query
                         .options(load_only(Project.slug, Project.title, Project.image))
                         .filter_by(is_featured=True, is_active=True)
                         ).limit(6).all()

    return render_template('projects.html',
                           projects=projects,
                           featured_projects=featured_projects,
                           project_types=PROJECT_TYPES,
                           current_type=project_type)


@main_bp.route('/du-an/<slug>')
def project_detail(slug):
    """Trang chi tiết dự án"""
    project = Project.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Tăng lượt xem
    project.view_count += 1
    db.session.commit()

    # Dự án liên quan
    related = (Project.query
    .options(load_only(Project.slug, Project.title, Project.image, Project.location))
    .filter(
        Project.id != project.id,
        Project.project_type == project.project_type,
        Project.is_active == True
    )
    ).limit(2).all()

    return render_template('project_detail.html',
                           project=project,
                           related=related)


# Route cũ redirect sang mới
@main_bp.route('/projects')
def old_projects():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.projects'), code=301)


@main_bp.route('/projects/<slug>')
def old_project_detail(slug):
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.project_detail', slug=slug), code=301)


# ==================== TUYỂN DỤNG ====================
@main_bp.route('/tuyen-dung')
def careers():
    """Trang tuyển dụng"""
    department = request.args.get('dept', '')
    location = request.args.get('loc', '')

    query = Job.query.filter_by(is_active=True)

    if department:
        query = query.filter_by(department=department)
    if location:
        query = query.filter_by(location=location)

    jobs = query.order_by(Job.is_urgent.desc(), Job.created_at.desc()).all()

    # Lấy danh sách phòng ban và địa điểm unique
    departments = db.session.query(Job.department).filter_by(is_active=True).distinct().all()
    locations = db.session.query(Job.location).filter_by(is_active=True).distinct().all()

    return render_template('careers.html',
                           jobs=jobs,
                           departments=[d[0] for d in departments if d[0]],
                           locations=[l[0] for l in locations if l[0]])


@main_bp.route('/tuyen-dung/<slug>')
def job_detail(slug):
    """Trang chi tiết tuyển dụng"""
    job = Job.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Tăng lượt xem
    job.view_count += 1
    db.session.commit()

    # Các vị trí khác
    other_jobs = Job.query.filter(
        Job.id != job.id,
        Job.is_active == True
    ).order_by(Job.is_urgent.desc()).limit(5).all()

    return render_template('job_detail.html',
                           job=job,
                           other_jobs=other_jobs)


# Route cũ redirect sang mới
@main_bp.route('/careers')
def old_careers():
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.careers'), code=301)


@main_bp.route('/careers/<slug>')
def old_job_detail(slug):
    """Redirect URL cũ sang URL mới"""
    return redirect(url_for('main.job_detail', slug=slug), code=301)


# ==================== SITEMAP.XML ====================
@main_bp.route('/sitemap.xml')
def sitemap():
    """Phục vụ file sitemap.xml"""
    sitemap_path = os.path.join(current_app.static_folder, 'sitemap.xml')
    if os.path.exists(sitemap_path):
        return send_from_directory(current_app.static_folder, 'sitemap.xml', mimetype='application/xml')
    else:
        abort(404, description="Sitemap not found")


# ==================== ROBOTS.TXT ====================
@main_bp.route('/robots.txt')
def robots_txt():
    """Phục vụ file robots.txt"""
    robots_path = os.path.join(current_app.static_folder, 'robots.txt')
    if os.path.exists(robots_path):
        return send_from_directory(current_app.static_folder, 'robots.txt', mimetype='text/plain')
    else:
        abort(404, description="Robots.txt not found")