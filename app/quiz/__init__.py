"""
Quiz Module - Hệ thống kiểm tra kiến thức nhân viên/ứng viên

Chức năng:
- Tạo đề thi với nhiều câu hỏi trắc nghiệm
- User làm bài không cần đăng nhập (chỉ nhập tên)
- Tính điểm tự động, hiển thị kết quả
- Admin quản lý đề, câu hỏi, xem điểm ứng viên
"""

from flask import Blueprint

# ==================== BLUEPRINTS ====================

# Blueprint cho user (public)
from app.quiz.routes import quiz_bp

# Blueprint cho admin (cần permission)
from app.quiz.admin_routes import quiz_admin_bp

__all__ = ['quiz_bp', 'quiz_admin_bp']