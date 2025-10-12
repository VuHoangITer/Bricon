"""
Data Management Package
=======================
Quản lý dữ liệu import/export cho hệ thống BRICON

Modules:
- import_products: Import sản phẩm từ JSON
- import_categories: Import danh mục từ JSON
"""

import os

# Đường dẫn đến thư mục data
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# Các file data
PRODUCTS_JSON = os.path.join(DATA_DIR, 'sanpham.json')
COMPANY_INFO_JSON = os.path.join(DATA_DIR, '..', 'chatbot', 'company_info.json')

__all__ = ['DATA_DIR', 'PRODUCTS_JSON', 'COMPANY_INFO_JSON']