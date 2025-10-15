import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    conn = db.engine.connect()

    # PostgreSQL: xóa tất cả dữ liệu trong bảng, bỏ qua foreign key
    conn.execute(text("""
        DO
        $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname='public') LOOP
                EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END;
        $$;
    """))
    conn.commit()
    print("✅ All data deleted (schema vẫn giữ nguyên)")
