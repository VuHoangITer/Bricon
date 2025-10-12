"""
SEO Keywords Configuration - BRICON VIETNAM
Tối ưu toàn diện cho ngành Keo dán gạch - Chà ron - Chống thấm - Phụ gia xây dựng.
Mục tiêu: Khi người dùng tìm bất kỳ từ khóa 'keo ...', 'ron ...', 'chống thấm ...' → xuất hiện BRICON.
"""

# =============================
# 🎯 Keywords SEO theo cấp độ
# =============================

MEDIA_KEYWORDS = {
    # ====== Từ khóa chính (Primary Keywords) ======
    'primary': [
        'keo dán gạch BRICON',
        'keo chà ron BRICON',
        'chống thấm BRICON',
        'keo ốp lát gạch BRICON',
        'keo dán gạch cao cấp BRICON',
        'keo dán gạch nội thất BRICON',
        'keo dán gạch ngoại thất BRICON',
        'ron epoxy BRICON',
        'keo dán gạch và chà ron BRICON',
        'keo dán gạch chống thấm BRICON',
        'vật liệu xây dựng hoàn thiện BRICON'
    ],

    # ====== Từ khóa phụ (Secondary Keywords) ======
    'secondary': [
        # nhóm keo dán gạch
        'keo dán gạch cao cấp',
        'keo dán gạch tốt nhất hiện nay',
        'keo dán gạch chống thấm nước',
        'keo dán gạch chịu nhiệt',
        'keo dán gạch ngoài trời',
        'keo ốp tường phòng tắm',
        'keo ốp lát nhà vệ sinh',
        'keo lát nền nhà bếp',
        'keo dán gạch hồ bơi',
        'keo dán gạch ban công',
        'keo dán gạch kháng kiềm',
        'keo dán gạch tiết kiệm',
        'keo dán gạch dễ thi công',

        # nhóm chà ron
        'keo chà ron chống ố mốc',
        'keo chà ron chống thấm nước',
        'keo chà ron bền màu',
        'keo chà ron epoxy hai thành phần',
        'keo chà ron sàn nhà tắm',
        'ron chống bám bẩn',
        'ron epoxy ngoại thất',
        'ron sàn gạch men',
        'ron chống rêu mốc',
        'ron epoxy cao cấp',

        # nhóm chống thấm
        'sơn chống thấm tường ngoài trời',
        'chống thấm sàn nhà vệ sinh',
        'chống thấm mái nhà',
        'chống thấm hồ nước',
        'chống thấm bê tông',
        'chống thấm nhà ở dân dụng',
        'chống thấm công trình xây dựng',

        # nhóm phụ gia & vật liệu
        'phụ gia xây dựng BRICON',
        'cát sấy UB BRICON',
        'vật liệu hoàn thiện công trình',
        'keo ron epoxy chống ố mới',
        'keo chống thấm gốc xi măng',
        'keo chà ron màu thời trang',
        'vật liệu xây dựng cao cấp',
        'giải pháp hoàn thiện công trình Việt'
    ],

    # ====== Thương hiệu (Brand Keywords) ======
    'brand': [
        'BRICON Việt Nam',
        'Công ty TNHH BRICON Việt Nam',
        'Keo của người Việt',
        'Tự hào keo Việt',
        'BRICON Adhesive',
        'BRICON Tile Adhesive',
        'Bricon Grout',
        'Keo BRICON',
        'BRICON chống thấm',
        'BRICON vật liệu xây dựng'
    ],

    # ====== Từ khóa chung ngành (General Keywords) ======
    'general': [
        'keo dán gạch',
        'keo chà ron',
        'keo ron epoxy',
        'keo ốp lát',
        'chống thấm',
        'chống thấm tường',
        'chống thấm sàn',
        'phụ gia xây dựng',
        'vật liệu xây dựng',
        'keo lát gạch',
        'keo ron sàn',
        'ron epoxy cao cấp',
        'ron màu trang trí',
        'vật liệu chống thấm nước',
        'keo ốp lát gạch men',
        'keo thi công gạch đá',
        'sản phẩm xây dựng Việt Nam',
        'keo công trình dân dụng',
        'keo hoàn thiện nội thất',
        'keo chống bong tróc',
        'vật liệu xây dựng thân thiện môi trường'
    ]
}

# =============================
# ⚖️ Scoring weights (ưu tiên thứ tự quan trọng cho SEO)
# =============================
KEYWORD_SCORES = {
    'primary': 25,           # Có keyword chính BRICON + sản phẩm
    'secondary_brand': 20,   # Keyword phụ + thương hiệu
    'secondary': 15,         # Keyword phụ
    'brand': 10,             # Chỉ có thương hiệu BRICON
    'general': 5             # Chỉ có keyword chung ngành
}

