"""
Decorators cho phân quyền (RBAC)
"""
from functools import wraps
from flask import flash, redirect, url_for, abort, request
from flask_login import current_user


# ==================== BACKWARD COMPATIBILITY ====================

def admin_required(f):
    """
    Đã chuyển qua permissions rồi giữ code để tránh lỗi :D
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập!', 'warning')
            return redirect(url_for('admin.login', next=request.url))

        if not current_user.is_admin:
            flash('Bạn không có quyền truy cập chức năng này!', 'danger')
            return redirect(url_for('admin.dashboard'))

        return f(*args, **kwargs)

    return decorated_function


# ==================== RBAC DECORATORS ====================

def permission_required(permission_name):
    """
    Decorator kiểm tra permission cụ thể

    Args:
        permission_name (str): Tên permission (vd: 'manage_products')

    Usage:
        @permission_required('manage_products')
        def add_product():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập!', 'warning')
                return redirect(url_for('admin.login', next=request.url))

            if not current_user.has_permission(permission_name):
                flash(f'Bạn không có quyền: {permission_name}', 'danger')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def role_required(*role_names):
    """
    Decorator kiểm tra role (có thể nhiều role)

    Args:
        *role_names: Tên các roles (vd: 'admin', 'editor')

    Usage:
        @role_required('admin', 'editor')
        def edit_blog():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập!', 'warning')
                return redirect(url_for('admin.login', next=request.url))

            if not current_user.role_obj or current_user.role_obj.name not in role_names:
                flash('Bạn không có quyền truy cập!', 'danger')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def any_permission_required(*permission_names):
    """
    Yêu cầu ít nhất 1 trong các quyền

    Args:
        *permission_names: Danh sách permissions

    Usage:
        @any_permission_required('edit_all_blogs', 'edit_own_blog')
        def edit_blog():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập!', 'warning')
                return redirect(url_for('admin.login', next=request.url))

            if not current_user.has_any_permission(*permission_names):
                flash('Bạn không có quyền thực hiện hành động này!', 'danger')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def all_permissions_required(*permission_names):
    """
    Yêu cầu tất cả các quyền

    Args:
        *permission_names: Danh sách permissions

    Usage:
        @all_permissions_required('manage_users', 'assign_roles')
        def change_user_role():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập!', 'warning')
                return redirect(url_for('admin.login', next=request.url))

            if not current_user.has_all_permissions(*permission_names):
                flash('Bạn không có đủ quyền thực hiện hành động này!', 'danger')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def owns_resource_or_admin(get_resource_owner):
    """
    Kiểm tra user sở hữu resource hoặc là admin

    Args:
        get_resource_owner: Function trả về owner_id của resource

    Usage:
        @owns_resource_or_admin(lambda id: Blog.query.get_or_404(id).author_id)
        def edit_blog(id):
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập!', 'warning')
                return redirect(url_for('admin.login', next=request.url))

            # Admin luôn có quyền
            if current_user.is_admin:
                return f(*args, **kwargs)

            # Kiểm tra ownership
            resource_owner_id = get_resource_owner(**kwargs)
            if resource_owner_id != current_user.id:
                flash('Bạn chỉ có thể chỉnh sửa nội dung của mình!', 'danger')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator