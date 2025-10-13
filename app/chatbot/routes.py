from flask import request, jsonify, session, current_app
from . import chatbot_bp
import google.generativeai as genai
from datetime import datetime
import json
import os

# ==================== BRICON CHATBOT ROUTES ====================

model = None  # Biến global cho Gemini model


def init_gemini():
    """Khởi tạo Gemini API"""
    global model
    api_key = current_app.config.get('GEMINI_API_KEY')
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
            current_app.logger.info("✅ Gemini API initialized successfully for BRICON Chatbot")
        except Exception as e:
            current_app.logger.error(f"❌ Failed to initialize Gemini API: {str(e)}")
            model = None
    else:
        current_app.logger.warning("⚠️ GEMINI_API_KEY not found in config")
        model = None


def load_company_info():
    """Đọc TOÀN BỘ thông tin công ty BRICON từ file JSON (KHÔNG giới hạn)"""
    json_path = os.path.join(current_app.root_path, 'chatbot', 'company_info.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            current_app.logger.info(f"✅ Loaded FULL company info from {json_path}")
            return data
    except FileNotFoundError:
        current_app.logger.error(f"❌ company_info.json not found at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        current_app.logger.error(f"❌ Invalid JSON in company_info.json: {str(e)}")
        return {}


def create_system_prompt(company_info):
    """Tạo system prompt TRẢ LỜI TRỰC TIẾP - KHÔNG DẮT"""
    company_name = company_info.get('company_name', 'CÔNG TY TNHH BRICON VIỆT NAM')
    slogan = company_info.get('slogan', 'Kết dính bền lâu – Xây dựng niềm tin')

    contact = company_info.get('contact', {})
    phone = contact.get('phone', '0901.180.094')
    hotline = contact.get('hotline', '1900 63 62 94')
    email = contact.get('email', 'info@bricon.vn')
    zalo = contact.get('zalo', phone)
    address = contact.get('address', '171 Đường An Phú Đông 03, Phường An Phú Đông, Quận 12, TP.HCM')
    website = contact.get('website', 'https://www.bricon.vn')
    working_hours = contact.get('working_hours', '8:00 - 17:30 (Thứ 2 - Thứ 7)')

    # Chi nhánh
    branches = contact.get('branches', [])
    branches_text = "\n".join([
        f"• {b.get('name', 'N/A')}: {b.get('address', 'N/A')}"
        for b in branches
    ])

    # TOÀN BỘ sản phẩm (KHÔNG giới hạn)
    products = company_info.get('products', [])
    products_text = ""
    if products:
        products_list = []
        for p in products:
            prod_info = f"\n━━━ {p.get('name', 'N/A')} ━━━"
            prod_info += f"\n• Loại: {p.get('category', 'N/A')}"
            prod_info += f"\n• Mô tả: {p.get('description', 'N/A')}"

            # Ứng dụng
            if p.get('application'):
                prod_info += "\n• Ứng dụng:"
                for app in p['application']:
                    prod_info += f"\n  - {app}"

            # Thông số kỹ thuật
            if p.get('technical_specs'):
                prod_info += "\n• Thông số kỹ thuật:"
                for key, val in p['technical_specs'].items():
                    prod_info += f"\n  - {key}: {val}"

            # Quy cách đóng gói
            if p.get('packaging'):
                prod_info += f"\n• Đóng gói: {p['packaging']}"

            # Màu sắc
            if p.get('colors'):
                prod_info += f"\n• Màu sắc: {', '.join(p['colors'])}"

            # Hạn sử dụng
            if p.get('expiry'):
                prod_info += f"\n• Hạn sử dụng: {p['expiry']}"

            products_list.append(prod_info)

        products_text = "\n".join(products_list)

    # TOÀN BỘ điểm mạnh
    strengths = company_info.get('strengths', [])
    strengths_text = "\n".join([f"✓ {s}" for s in strengths])

    # TOÀN BỘ FAQ
    faq = company_info.get('faq', [])
    faq_text = ""
    if faq:
        faq_text = "\n".join([
            f"❓ {q.get('question', '')}\n💡 {q.get('answer', '')}\n"
            for q in faq
        ])

    # Chính sách đổi trả CHI TIẾT
    return_policy = company_info.get('return_policy', {})
    return_summary = return_policy.get('policy_summary', 'Công ty có chính sách đổi trả linh hoạt')

    conditions = return_policy.get('conditions', {})
    conditions_parts = []
    for key, value in conditions.items():
        if isinstance(value, list):
            items = "\n".join([f"  • {item}" for item in value])
            conditions_parts.append(f"\n{key}:\n{items}")
        else:
            conditions_parts.append(f"\n{key}: {value}")
    conditions_text = "".join(conditions_parts)

    notes = return_policy.get('note', [])
    notes_text = "\n".join([f"⚠️ {note}" for note in notes]) if notes else ""

    # Quy trình đặt hàng
    process = company_info.get('process', [])
    process_text = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(process)])

    # Dự án tiêu biểu
    projects = company_info.get('projects', [])
    projects_text = "\n".join([f"• {proj}" for proj in projects[:15]]) if projects else "Nhiều dự án lớn"

    # Giới thiệu công ty
    company_intro = company_info.get('company_intro', '')

    prompt = f"""BẠN LÀ TRỢ LÝ ẢO BRICON - CHUYÊN GIA VẬT LIỆU XÂY DỰNG

╔═══════════════════════════════════════════════════════════════╗
║                    THÔNG TIN CÔNG TY                          ║
╚═══════════════════════════════════════════════════════════════╝

🏢 Tên: {company_name}
💡 Slogan: {slogan}
📞 Hotline: {hotline}
📱 Điện thoại: {phone}
💬 Zalo: {zalo}
📧 Email: {email}
🌐 Website: {website}
📍 Địa chỉ: {address}
⏰ Giờ làm việc: {working_hours}

📖 GIỚI THIỆU:
{company_intro}

╔═══════════════════════════════════════════════════════════════╗
║                    HỆ THỐNG CHI NHÁNH                         ║
╚═══════════════════════════════════════════════════════════════╝
{branches_text}

╔═══════════════════════════════════════════════════════════════╗
║                  DANH MỤC SẢN PHẨM CHI TIẾT                   ║
╚═══════════════════════════════════════════════════════════════╝
{products_text}

╔═══════════════════════════════════════════════════════════════╗
║                      ƯU ĐIỂM NỔI BẬT                          ║
╚═══════════════════════════════════════════════════════════════╝
{strengths_text}

╔═══════════════════════════════════════════════════════════════╗
║                   CHÍNH SÁCH ĐỔI TRẢ HÀNG                     ║
╚═══════════════════════════════════════════════════════════════╝
📌 {return_summary}

✅ ĐIỀU KIỆN ĐỔI TRẢ:{conditions_text}

{notes_text}

╔═══════════════════════════════════════════════════════════════╗
║                   QUY TRÌNH ĐẶT HÀNG                          ║
╚═══════════════════════════════════════════════════════════════╝
{process_text}

╔═══════════════════════════════════════════════════════════════╗
║                   DỰ ÁN TIÊU BIỂU                             ║
╚═══════════════════════════════════════════════════════════════╝
{projects_text}

╔═══════════════════════════════════════════════════════════════╗
║                   CÂU HỎI THƯỜNG GẶP                          ║
╚═══════════════════════════════════════════════════════════════╝
{faq_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NGUYÊN TẮC TRẢ LỜI - QUAN TRỌNG:

1. TRẢ LỜI TRỰC TIẾP VÀO TRỌNG TÂM:
   ✅ Khách hỏi gì → Trả lời NGAY điều đó
   ✅ Dùng thông tin từ database ở trên để trả lời CHÍNH XÁC
   ✅ KHÔNG dẫn dắt, KHÔNG hỏi lại nếu đã có đủ thông tin
   ✅ Chỉ hỏi thêm KHI THỰC SỰ CẦN làm rõ (VD: khách hỏi "keo dán gạch" mà có nhiều loại)

2. VỀ GIÁ CẢ:
   - KHÔNG đưa ra con số giá cụ thể
   - Hướng dẫn: "Anh/chị liên hệ {hotline} hoặc Zalo {zalo} để nhận báo giá tốt nhất ạ"

3. PHONG CÁCH:
   - Thân thiện, tự nhiên, chuyên nghiệp
   - Xưng hô: "Dạ", "Em", "Anh/Chị"
   - Emoji vừa phải: 😊 💪 🧱 📞 ✅
   - Câu ngắn gọn 2-4 câu (trừ khi cần giải thích kỹ thuật chi tiết)

4. XỬ LÝ ĐẶC BIỆT:
   - Nếu KHÔNG CÓ thông tin trong database → Thừa nhận và hướng dẫn liên hệ hotline
   - Nếu NGOÀI PHẠM VI (không liên quan BRICON) → Từ chối lịch sự và chuyển hướng về sản phẩm
   - Nếu CẦN THÔNG TIN THÊM → Hỏi ngắn gọn 1 câu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VÍ DỤ TRẢ LỜI TỐT:

❌ SAI (dẫn dắt không cần thiết):
Khách: "Keo dán gạch ngoại thất giá bao nhiêu?"
Bot: "Dạ BRICON có keo dán gạch ngoại thất rất tốt ạ. Anh/chị định dùng cho loại gạch nào để em tư vấn?"

✅ ĐÚNG (trả lời trực tiếp):
Khách: "Keo dán gạch ngoại thất giá bao nhiêu?"
Bot: "Dạ, keo dán gạch BRICON Ngoại Thất có giá tùy số lượng và chương trình khuyến mãi ạ. Anh/chị liên hệ 📞 {hotline} hoặc Zalo {zalo} để nhận báo giá chi tiết nhé!"

❌ SAI (thừa thông tin):
Khách: "Bao giờ giao hàng?"
Bot: "Dạ BRICON giao hàng rất nhanh ạ. Nội thành 1-2 ngày, các tỉnh 2-5 ngày. Anh/chị định đặt hàng cho khu vực nào, số lượng bao nhiêu để em tư vấn chi tiết hơn ạ?"

✅ ĐÚNG (đủ thông tin, không dư thừa):
Khách: "Bao giờ giao hàng?"
Bot: "Dạ, thời gian giao hàng:\n• Nội thành TP.HCM: 1-2 ngày 🚚\n• Các tỉnh: 2-5 ngày\nAnh/chị ở đâu để em tư vấn cụ thể hơn ạ?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HÃY BẮT ĐẦU TƯ VẤN - NHỚ: TRẢ LỜI THẲNG VÀO TRỌNG TÂM!
"""
    return prompt


@chatbot_bp.route('/send', methods=['POST'])
def send_message():
    """Xử lý tin nhắn từ người dùng gửi chatbot BRICON"""
    global model

    # Kiểm tra chatbot có được bật không
    if not current_app.config.get('CHATBOT_ENABLED', True):
        return jsonify({
            'response': '⚠️ Chatbot BRICON đang bảo trì. Vui lòng liên hệ:\n📞 Hotline: 1900 63 62 94\n💬 Zalo: 0901.180.094'
        }), 503

    # Khởi tạo model nếu chưa có
    if model is None:
        init_gemini()

    if model is None:
        return jsonify({
            'response': '😔 Xin lỗi, chatbot BRICON tạm thời không khả dụng.\n\nVui lòng liên hệ:\n📞 Hotline: 1900 63 62 94\n💬 Zalo: 0901.180.094\n📧 Email: info@bricon.vn'
        }), 500

    try:
        # Lấy tin nhắn từ request
        data = request.json
        user_message = data.get('message', '').strip()

        # Validate tin nhắn
        if not user_message:
            return jsonify({'error': 'Tin nhắn không được để trống'}), 400

        if len(user_message) > 500:
            return jsonify({'error': 'Tin nhắn quá dài. Vui lòng nhập tối đa 500 ký tự'}), 400

        # Kiểm tra và khởi tạo session
        if 'chatbot_request_count' not in session:
            session['chatbot_request_count'] = 0
            session['chatbot_request_start_time'] = datetime.now().timestamp()

        # Kiểm tra giới hạn request
        current_time = datetime.now().timestamp()
        request_limit = current_app.config.get('CHATBOT_REQUEST_LIMIT', 30)
        window = current_app.config.get('CHATBOT_REQUEST_WINDOW', 3600)  # 1 giờ

        # Reset counter nếu hết thời gian window
        if current_time - session['chatbot_request_start_time'] > window:
            session['chatbot_request_count'] = 0
            session['chatbot_request_start_time'] = current_time

        # Kiểm tra đã vượt giới hạn chưa
        if session['chatbot_request_count'] >= request_limit:
            return jsonify({
                'response': f'⏰ Anh/chị đã sử dụng hết {request_limit} lượt chat miễn phí trong 1 giờ.\n\n'
                            f'Vui lòng thử lại sau hoặc liên hệ trực tiếp:\n'
                            f'📞 Hotline: 1900 63 62 94\n'
                            f'💬 Zalo: 0901.180.094\n'
                            f'📧 Email: info@bricon.vn\n\n'
                            f'Cảm ơn anh/chị đã quan tâm đến BRICON! 😊'
            })

        # Tăng counter
        session['chatbot_request_count'] += 1

        # Khởi tạo lịch sử chat
        if 'chatbot_history' not in session:
            session['chatbot_history'] = []

        # Lấy lịch sử 5 tin nhắn gần nhất
        history_context = "\n".join([
            f"{'Khách' if msg['role'] == 'user' else 'Bot'}: {msg['content']}"
            for msg in session['chatbot_history'][-5:]
        ])

        # Tạo prompt
        company_info = load_company_info()
        system_prompt = create_system_prompt(company_info)

        full_prompt = f"""{system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📜 LỊCH SỬ HỘI THOẠI:
{history_context if history_context else "(Hội thoại mới)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 TIN NHẮN MỚI:
{user_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ TRẢ LỜI (nhớ: TRỰC TIẾP VÀO TRỌNG TÂM, KHÔNG DẮT):
"""

        # Gọi Gemini API
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.6,  # Giảm xuống để câu trả lời tập trung hơn
                    max_output_tokens=800,  # Tăng lên để có thể trả lời chi tiết khi cần
                    top_p=0.9,
                    top_k=40
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            bot_reply = getattr(response, 'text', '').strip()

            # Fallback nếu không có response
            if not bot_reply:
                bot_reply = (
                    "😔 Dạ xin lỗi, em chưa có đủ thông tin để trả lời câu hỏi này.\n\n"
                    "Anh/chị vui lòng liên hệ:\n"
                    "📞 Hotline: 1900 63 62 94\n"
                    "💬 Zalo: 0901.180.094\n"
                    "để được hỗ trợ nhanh nhất nhé!"
                )

        except Exception as api_error:
            current_app.logger.error(f"❌ Gemini API error: {str(api_error)}")
            return jsonify({
                'response': '⚠️ Hệ thống đang quá tải. Anh/chị vui lòng:\n'
                            '• Thử lại sau vài giây\n'
                            '• Hoặc gọi 📞 1900 63 62 94 để được hỗ trợ ngay 😊'
            }), 500

        # Lưu lịch sử
        session['chatbot_history'].append({'role': 'user', 'content': user_message})
        session['chatbot_history'].append({'role': 'assistant', 'content': bot_reply})

        # Giới hạn lịch sử 20 tin nhắn gần nhất
        session['chatbot_history'] = session['chatbot_history'][-20:]
        session.modified = True

        # Tính số lượt còn lại
        remaining = request_limit - session['chatbot_request_count']

        return jsonify({
            'response': bot_reply,
            'remaining_requests': remaining,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"❌ Chatbot error: {str(e)}", exc_info=True)
        return jsonify({
            'response': '😔 Đã có lỗi xảy ra. Vui lòng liên hệ BRICON:\n'
                        '📞 Hotline: 1900 63 62 94\n'
                        '💬 Zalo: 0901.180.094\n'
                        '📧 Email: info@bricon.vn'
        }), 500


@chatbot_bp.route('/reset', methods=['POST'])
def reset_chat():
    """Làm mới hội thoại BRICON"""
    try:
        # Xóa toàn bộ dữ liệu session chatbot
        session.pop('chatbot_history', None)
        session.pop('chatbot_request_count', None)
        session.pop('chatbot_request_start_time', None)
        session.modified = True

        current_app.logger.info("✅ Chat history reset successfully")

        return jsonify({
            'status': 'success',
            'message': '✅ Đã làm mới hội thoại thành công!',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"❌ Reset chat error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '⚠️ Không thể làm mới hội thoại. Vui lòng thử lại!'
        }), 500


@chatbot_bp.route('/status', methods=['GET'])
def chatbot_status():
    """Kiểm tra trạng thái chatbot"""
    try:
        global model

        status = {
            'enabled': current_app.config.get('CHATBOT_ENABLED', True),
            'model_initialized': model is not None,
            'request_limit': current_app.config.get('CHATBOT_REQUEST_LIMIT', 30),
            'remaining_requests': current_app.config.get('CHATBOT_REQUEST_LIMIT', 30) - session.get(
                'chatbot_request_count', 0),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(status)

    except Exception as e:
        current_app.logger.error(f"❌ Status check error: {str(e)}")
        return jsonify({'error': 'Unable to check status'}), 500


# ==================== KHỞI TẠO KHI APP CHẠY ====================
def init_chatbot(app):
    """Hàm khởi tạo chatbot khi app khởi động"""
    with app.app_context():
        init_gemini()
        current_app.logger.info("🤖 BRICON Chatbot initialized")