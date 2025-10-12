"""
Script Import Sản Phẩm BRICON từ sanpham.json
==============================================
Chạy từ thư mục gốc: python -m app.data.import_products

Tính năng:
- Import categories và products từ sanpham.json
- Tự động tạo slug từ tên
- Cập nhật nếu sản phẩm đã tồn tại
- Validate dữ liệu đầy đủ
- Log chi tiết quá trình import
"""

import json
import os
import sys
from datetime import datetime
from slugify import slugify

# Thêm đường dẫn để import được
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db
from app.models import Product, Category
from app.data import PRODUCTS_JSON


class ProductImporter:
    """Class xử lý import sản phẩm"""

    def __init__(self, json_file=None):
        self.app = create_app()
        self.json_file = json_file or PRODUCTS_JSON
        self.stats = {
            'categories_created': 0,
            'categories_updated': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': 0,
            'skipped': 0
        }
        self.categories_map = {}

    def load_json_data(self):
        """Đọc dữ liệu từ file JSON"""
        if not os.path.exists(self.json_file):
            print(f"❌ Không tìm thấy file: {self.json_file}")
            return None

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print("\n" + "=" * 70)
            print("📦 THÔNG TIN FILE DỮ LIỆU")
            print("=" * 70)
            print(f"📄 File: {os.path.basename(self.json_file)}")
            print(f"📊 Version: {data.get('version', 'N/A')}")
            print(f"📅 Cập nhật: {data.get('last_updated', 'N/A')}")
            print(f"📦 Tổng sản phẩm: {data.get('total_products', 0)}")
            print(f"📂 Tổng danh mục: {len(data.get('categories', []))}")
            print("=" * 70 + "\n")

            return data

        except json.JSONDecodeError as e:
            print(f"❌ Lỗi đọc JSON tại dòng {e.lineno}: {e.msg}")
            return None
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return None

    def import_categories(self, categories_data):
        """Import danh mục sản phẩm"""
        if not categories_data:
            print("⚠️  Không có danh mục nào để import")
            return {}

        print("\n" + "=" * 70)
        print("📂 IMPORT DANH MỤC SẢN PHẨM")
        print("=" * 70)

        with self.app.app_context():
            for idx, cat_data in enumerate(categories_data, 1):
                try:
                    cat_name = cat_data.get('name')
                    if not cat_name:
                        print(f"⚠️  [{idx}] Bỏ qua: Thiếu tên danh mục")
                        self.stats['skipped'] += 1
                        continue

                    cat_slug = cat_data.get('slug') or slugify(cat_name)

                    # Tìm hoặc tạo mới category
                    category = Category.query.filter_by(slug=cat_slug).first()

                    if category:
                        # Cập nhật
                        category.name = cat_name
                        category.description = cat_data.get('description', '')
                        category.image = cat_data.get('image')
                        # ❌ REMOVED: meta_description (không có trong Category model)

                        print(f"📝 [{idx}] Cập nhật: {cat_name}")
                        self.stats['categories_updated'] += 1
                    else:
                        # Tạo mới
                        category = Category(
                            name=cat_name,
                            slug=cat_slug,
                            description=cat_data.get('description', ''),
                            image=cat_data.get('image'),
                            # ❌ REMOVED: meta_description (không có trong Category model)
                            is_active=True
                        )
                        db.session.add(category)
                        db.session.flush()  # Để lấy ID

                        print(f"✅ [{idx}] Tạo mới: {cat_name} (ID: {category.id})")
                        self.stats['categories_created'] += 1

                    # Lưu vào map
                    self.categories_map[cat_name] = category.id


                except Exception as e:
                    print(f"❌ [{idx}] Lỗi: {cat_data.get('name', 'Unknown')} - {str(e)}")
                    self.stats['errors'] += 1
                    db.session.rollback()
                    continue

            # Commit categories
            try:
                db.session.commit()
                print(f"\n💾 Đã lưu {len(self.categories_map)} danh mục vào database")
            except Exception as e:
                print(f"\n❌ Lỗi commit categories: {e}")
                db.session.rollback()
                return {}

        return self.categories_map

    def import_products(self, products_data):
        """Import sản phẩm"""
        if not products_data:
            print("\n⚠️  Không có sản phẩm nào để import")
            return

        print("\n" + "=" * 70)
        print("🧱 IMPORT SẢN PHẨM")
        print("=" * 70)

        with self.app.app_context():
            for idx, prod_data in enumerate(products_data, 1):
                try:
                    prod_name = prod_data.get('name')
                    if not prod_name:
                        print(f"⚠️  [{idx}] Bỏ qua: Thiếu tên sản phẩm")
                        self.stats['skipped'] += 1
                        continue

                    # Lấy category_id thay vì đối tượng category
                    cat_name = prod_data.get('category')
                    if cat_name not in self.categories_map:
                        print(f"⚠️  [{idx}] Bỏ qua {prod_name}: Không tìm thấy danh mục '{cat_name}'")
                        self.stats['skipped'] += 1
                        continue

                    category_id = self.categories_map[cat_name]
                    prod_slug = prod_data.get('slug') or slugify(prod_name)

                    # Tìm hoặc tạo mới product
                    product = Product.query.filter_by(slug=prod_slug).first()

                    if product:
                        # Cập nhật
                        product.name = prod_name
                        product.description = prod_data.get('description', '')
                        product.category_id = category_id
                        product.image = prod_data.get('image')
                        product.price = prod_data.get('price', 0)
                        product.old_price = prod_data.get('old_price')
                        product.is_featured = prod_data.get('is_featured', False)

                        # Thông tin kỹ thuật
                        product.composition = prod_data.get('composition')
                        product.production = prod_data.get('production')
                        product.application = prod_data.get('application')
                        product.expiry = prod_data.get('expiry')
                        product.packaging = prod_data.get('packaging')
                        product.colors = prod_data.get('colors')
                        product.technical_specs = prod_data.get('technical_specs')
                        product.standards = prod_data.get('standards')

                        # ❌ REMOVED: brand (không có trong Product model)
                        # ❌ REMOVED: meta_description (không có trong Product model)
                        # ❌ REMOVED: meta_keywords (không có trong Product model)

                        product.updated_at = datetime.utcnow()

                        print(f"📝 [{idx}] Cập nhật: {prod_name}")
                        self.stats['products_updated'] += 1

                    else:
                        # Tạo mới
                        product = Product(
                            name=prod_name,
                            slug=prod_slug,
                            description=prod_data.get('description', ''),
                            category_id=category_id,
                            image=prod_data.get('image'),
                            price=prod_data.get('price', 0),
                            old_price=prod_data.get('old_price'),
                            is_featured=prod_data.get('is_featured', True),
                            is_active=True,

                            # Thông tin kỹ thuật
                            composition=prod_data.get('composition'),
                            production=prod_data.get('production'),
                            application=prod_data.get('application'),
                            expiry=prod_data.get('expiry'),
                            packaging=prod_data.get('packaging'),
                            colors=prod_data.get('colors'),
                            technical_specs=prod_data.get('technical_specs'),
                            standards=prod_data.get('standards'),

                            # ❌ REMOVED: brand (không có trong Product model)
                            # ❌ REMOVED: meta_description (không có trong Product model)
                            # ❌ REMOVED: meta_keywords (không có trong Product model)
                        )
                        db.session.add(product)

                        print(f"✅ [{idx}] Tạo mới: {prod_name}")
                        self.stats['products_created'] += 1

                    # Commit từng sản phẩm để tránh rollback toàn bộ khi lỗi
                    db.session.commit()

                except Exception as e:
                    print(f"❌ [{idx}] Lỗi: {prod_data.get('name', 'Unknown')} - {str(e)}")
                    self.stats['errors'] += 1
                    db.session.rollback()
                    continue

    def print_summary(self):
        """In tổng kết"""
        print("\n" + "=" * 70)
        print("📊 TỔNG KẾT IMPORT")
        print("=" * 70)
        print(f"📂 Danh mục:")
        print(f"   ✅ Tạo mới:    {self.stats['categories_created']}")
        print(f"   📝 Cập nhật:   {self.stats['categories_updated']}")
        print(f"\n🧱 Sản phẩm:")
        print(f"   ✅ Tạo mới:    {self.stats['products_created']}")
        print(f"   📝 Cập nhật:   {self.stats['products_updated']}")
        print(f"\n⚠️  Bỏ qua:      {self.stats['skipped']}")
        print(f"❌ Lỗi:         {self.stats['errors']}")
        print("=" * 70)

        total_success = (
                self.stats['categories_created'] +
                self.stats['categories_updated'] +
                self.stats['products_created'] +
                self.stats['products_updated']
        )

        if total_success > 0:
            print(f"\n🎉 Hoàn tất! Đã xử lý thành công {total_success} mục")

        if self.stats['errors'] > 0:
            print(f"⚠️  Có {self.stats['errors']} lỗi trong quá trình import")

    def run(self):
        """Chạy toàn bộ quá trình import"""
        print("\n" + "🚀 " * 35)
        print("   BRICON - IMPORT SẢN PHẨM TỪ JSON")
        print("🚀 " * 35)

        # Load dữ liệu
        data = self.load_json_data()
        if not data:
            print("\n❌ Không thể đọc dữ liệu. Dừng import.")
            return False

        # Xác nhận
        print("\n⚠️  Bạn có chắc muốn import dữ liệu?")
        print("   (Dữ liệu cũ sẽ được CẬP NHẬT nếu trùng slug)")
        confirm = input("\n👉 Nhập 'yes' để tiếp tục: ").strip().lower()

        if confirm != 'yes':
            print("\n❌ Đã hủy import")
            return False

        # Import categories
        categories = data.get('categories', [])
        self.import_categories(categories)

        if not self.categories_map:
            print("\n❌ Không có danh mục nào được import. Dừng import sản phẩm.")
            return False

        # Import products
        products = data.get('products', [])
        self.import_products(products)

        # Tổng kết
        self.print_summary()

        return True


def main():
    """Hàm chính"""
    try:
        importer = ProductImporter()
        success = importer.run()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy import bởi người dùng")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()