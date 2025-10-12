"""
Project Configuration - BRICON VIETNAM
Danh mục & cấu hình các loại dự án tiêu biểu sử dụng sản phẩm BRICON:
Keo dán gạch – Keo chà ron – Chống thấm – Phụ gia xây dựng.
"""

PROJECT_TYPES = [
    {
        'value': 'commercial',
        'label': 'Trung tâm thương mại & khách sạn',
        'icon': 'bi-shop-window',
        'description': 'Các tổ hợp trung tâm thương mại, khách sạn, khu nghỉ dưỡng cao cấp sử dụng keo dán gạch và keo chà ron BRICON.',
        'examples': [
            'Tổ hợp Trung tâm thương mại và Khách sạn Hoàng Đế',
            'Khách sạn Queen Ann – Nha Trang',
            'Pullman Saigon Centre – TP.HCM',
            'Saigon Centre – TP.HCM',
            'Khu du lịch biển Blue Sapphire Resort'
        ]
    },
    {
        'value': 'resort_golf',
        'label': 'Khu du lịch & sân golf',
        'icon': 'bi-flag',
        'description': 'Các dự án nghỉ dưỡng, resort và sân golf đẳng cấp có sử dụng keo ốp lát, chống thấm và ron epoxy BRICON.',
        'examples': [
            'Dự án Tòa nhà Câu lạc bộ Golf Đà Lạt',
            'Nara Bình Tiên Golf Club – Bình Thuận',
            'Dự án Novaworld – Phan Thiết',
            'Dự án biệt thự Wyndham Garden Phú Quốc',
            'Swanbay Đại Phước'
        ]
    },
    {
        'value': 'residential',
        'label': 'Nhà ở & Chung cư cao cấp',
        'icon': 'bi-building',
        'description': 'Các công trình căn hộ, chung cư, biệt thự, khu dân cư cao cấp hoàn thiện bằng keo dán gạch và keo chà ron BRICON.',
        'examples': [
            'Chung cư Icon 56 – TP.HCM',
            'Chung cư Bộ đội Biên phòng – TP.HCM',
            'Cao ốc Long Thịnh – TP.HCM',
            'Vinhome Golden River Ba Son',
            'Dự án Dream City'
        ]
    },
    {
        'value': 'industrial',
        'label': 'Nhà máy & công trình công nghiệp',
        'icon': 'bi-gear-wide-connected',
        'description': 'Các nhà máy, kho xưởng, khu công nghiệp yêu cầu độ bám dính, chịu lực và chống thấm cao.',
        'examples': [
            'Nhà máy Hwasung Vina – Đồng Nai',
            'Nhà máy dược Zuellig Pharma – TP.HCM'
        ]
    },
    {
        'value': 'public',
        'label': 'Công trình công cộng & hạ tầng',
        'icon': 'bi-bank',
        'description': 'Công trình hành chính, bệnh viện, cơ sở y tế và hạ tầng kỹ thuật sử dụng keo dán gạch, chống thấm BRICON.',
        'examples': [
            'Bệnh viện Vinmec – Nha Trang',
            'Bệnh viện Đa khoa Đồng Nai',
            'Sở Xây dựng Đồng Nai'
        ]
    }
]

# =============================
# WTForms choices & lookup dict
# =============================
PROJECT_TYPE_CHOICES = [(pt['value'], pt['label']) for pt in PROJECT_TYPES]
PROJECT_TYPE_DICT = {pt['value']: pt for pt in PROJECT_TYPES}
