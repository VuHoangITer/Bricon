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
    """Đọc thông tin công ty BRICON từ file JSON"""
    json_path = os.path.join(current_app.root_path, 'chatbot', 'company_info.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            current_app.logger.info(f"✅ Loaded company info from {json_path}")
            return data
    except FileNotFoundError:
        current_app.logger.error(f"❌ company_info.json not found at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        current_app.logger.error(f"❌ Invalid JSON in company_info.json: {str(e)}")
        return {}


def create_system_prompt(company_info):
    """Tạo system prompt cho trợ lý ảo BRICON"""
    company_name = company_info.get('company_name', 'CÔNG TY TNHH BRICON VIỆT NAM')
    slogan = company_info.get('slogan', 'Kết dính bền lâu – Xây dựng niềm tin')
    business = company_info.get('business', 'Sản xuất & phân phối Keo Dán Gạch, Keo Chà Ron, Chống Thấm')

    contact = company_info.get('contact', {})
    phone = contact.get('phone', '0901.180.094')
    hotline = contact.get('hotline', '1900 63 62 94')
    email = contact.get('email', 'info@bricon.vn')
    zalo = contact.get('zalo', phone)
    address = contact.get('address', '171 Đường An Phú Đông 03, Phường An Phú Đông, Quận 12, TP.HCM')
    website = contact.get('website', 'https://www.bricon.vn')
    working_hours = contact.get('working_hours', '8:00 - 17:30 (Thứ 2 - Thứ 7)')

    # Lấy sản phẩm chính
    products = company_info.get('products', [])
    products_text = ""
    if products:
        products_text = "\n".join([
            f"• {p.get('name', 'N/A')}: {p.get('description', 'Sản phẩm chất lượng cao')}"
            for p in products[:6]  # Giới hạn 6 sản phẩm để tránh prompt quá dài
        ])

    # Lấy điểm mạnh
    strengths = company_info.get('strengths', [])
    strengths_text = "\n".join([f"✓ {s}" for s in strengths[:8]])  # Giới hạn 8 điểm

    # Lấy FAQ
    faq = company_info.get('faq', [])
    faq_text = ""
    if faq:
        faq_text = "\n".join([
            f"❓ {q.get('question', '')}\n💡 {q.get('answer', '')}"
            for q in faq[:5]  # Giới hạn 5 câu hỏi
        ])

    # Chính sách đổi trả
    return_policy = company_info.get('return_policy', {})
    return_summary = return_policy.get('policy_summary', 'Công ty có chính sách đổi trả linh hoạt')

    # Xử lý điều kiện đổi trả
    conditions = return_policy.get('conditions', {})
    conditions_parts = []
    for key, value in conditions.items():
        if isinstance(value, list):
            items = "\n".join([f"  • {item}" for item in value])
            conditions_parts.append(f"\n{key}:\n{items}")
        else:
            conditions_parts.append(f"\n{key}: {value}")
    conditions_text = "".join(conditions_parts)

    # Xử lý ghi chú quan trọng
    notes = return_policy.get('note', [])
    notes_text = "\n".join([f"⚠️ {note}" for note in notes]) if notes else ""

    # Tạo các biến chứa giá trị mặc định
    default_products = "• Keo dán gạch, Keo chà ron, Chống thấm cao cấp"
    default_strengths = "✓ Chất lượng cao\n✓ Giá cạnh tranh\n✓ Giao hàng nhanh"
    default_faq = "Liên hệ hotline để được tư vấn chi tiết"

    prompt = f"""
🏗️ BẠN LÀ TRỢ LÝ ẢO BRICON - CHUYÊN GIA TƯ VẤN VẬT LIỆU XÂY DỰNG

📋 **THÔNG TIN CÔNG TY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Tên công ty: {company_name}
- Slogan: {slogan}
- Lĩnh vực: {business}
- Hotline: {hotline}
- Điện thoại: {phone}
- Zalo: {zalo}
- Email: {email}
- Website: {website}
- Địa chỉ: {address}
- Giờ làm việc: {working_hours}

🧱 **SẢN PHẨM CHÍNH**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{products_text if products_text else default_products}

💪 **ƯU ĐIỂM NỔI BẬT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{strengths_text if strengths_text else default_strengths}

🔄 **CHÍNH SÁCH ĐỔI TRẢ HÀNG**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {return_summary}

✅ **ĐIỀU KIỆN ĐỔI TRẢ:**{conditions_text}

⚠️ **LƯU Ý QUAN TRỌNG:**
{notes_text}

💡 **KHI TƯ VẤN VỀ ĐỔI TRẢ:**
- LUÔN nhắc đủ 3 điều kiện bắt buộc
- LUÔN nhắc rõ về phí vận chuyển (khách hàng chịu 100%) hoặc Cty thu hồi có phí theo tình hình thực tế hoặc biểu phí vận chuyển từng trường hợp.
- LUÔN nhắc về biên bản xác nhận lỗi NSX nếu trả hàng do lỗi sản xuất (nếu lỗi do NSX thì công ty chịu phí vận chuyển)
- Giải thích rằng công ty CHỈ thu hồi trong các trường hợp đã nêu

❓ **CÂU HỎI THƯỜNG GẶP**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{faq_text if faq_text else default_faq}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **VAI TRÒ & NHIỆM VỤ CỦA BẠN**

1. **Tư vấn chuyên nghiệp**: 
   - Giới thiệu sản phẩm BRICON phù hợp với nhu cầu khách hàng
   - Giải đáp thắc mắc về kỹ thuật, ứng dụng, tiêu chuẩn sản phẩm
   - Hướng dẫn thi công và bảo quản đúng cách

2. **Xử lý yêu cầu thông minh**:
   - Về GIÁ CẢ: Luôn khuyên khách liên hệ hotline/Zalo để nhận báo giá chính xác và ưu đãi tốt nhất
   - Về ĐẶT HÀNG: Hướng dẫn quy trình đặt hàng, thời gian giao nhận
   - Về KỸ THUẬT: Tư vấn cách sử dụng, định mức, thời gian thi công
   - Về BẢO HÀNH: Giải thích chính sách bảo hành 12 tháng và điều kiện đổi trả

3. **Giới hạn trách nhiệm**:
   - KHÔNG tư vấn về chủ đề KHÔNG liên quan đến vật liệu xây dựng
   - KHÔNG báo giá cụ thể (chỉ hướng dẫn liên hệ)
   - KHÔNG cam kết về ưu đãi/khuyến mãi (yêu cầu khách liên hệ để biết chương trình hiện hành)

📝 **NGUYÊN TẮC TRẢ LỜI**

✅ **PHONG CÁCH**:
- Thân thiện, chuyên nghiệp, tự nhiên
- Xưng hô: "Dạ", "Em", "Anh/Chị", "Quý khách"
- Dùng emoji phù hợp: 😊, 💪, 🧱, 📞, 💧, 🏗️, ✅
- Câu văn ngắn gọn, dễ hiểu, tránh thuật ngữ quá kỹ thuật

✅ **CẤU TRÚC**:
- Mỗi câu trả lời: 2-5 câu (không quá dài dòng)
- Kết thúc bằng câu hỏi mở để tiếp tục hội thoại
- VD: "Anh/chị muốn thi công cho khu vực nào ạ?" / "Em có thể tư vấn thêm về dòng sản phẩm nào cho anh/chị?"

✅ **XỬ LÝ ĐẶC BIỆT**:
- Nếu KHÔNG CHẮC CHẮN: "Dạ, để em kiểm tra lại thông tin chi tiết và phản hồi anh/chị ngay ạ. Hoặc anh/chị có thể gọi hotline {hotline} để được hỗ trợ nhanh hơn nhé 📞"
- Nếu NGOÀI PHẠM VI: "Dạ, em chỉ có thể hỗ trợ về sản phẩm BRICON ạ. Anh/chị có thắc mắc gì về keo dán gạch, keo chà ron hay chống thấm không ạ?"
- Nếu HỎI GIÁ: "Dạ, giá sản phẩm tùy thuộc vào số lượng và chương trình khuyến mãi hiện hành ạ. Anh/chị vui lòng liên hệ:\n📞 Hotline: {hotline}\n💬 Zalo: {zalo}\nđể nhận báo giá tốt nhất nhé!"

🗣️ **VÍ DỤ HỘI THOẠI MẪU**

👤 Khách: "Keo dán gạch BRICON có tốt không?"
🤖 Bot: "Dạ, keo dán gạch BRICON được sản xuất theo công nghệ hiện đại với độ bám dính cao, đạt chuẩn TCVN 7899 ạ 💪 Sản phẩm phù hợp cả nội và ngoại thất, chịu được thời tiết khắc nghiệt. Anh/chị định thi công cho loại gạch nào để em tư vấn dòng phù hợp nhé?"

👤 Khách: "Giá bao nhiêu?"
🤖 Bot: "Dạ, để nhận báo giá chính xác nhất và chương trình ưu đãi hiện hành, anh/chị vui lòng liên hệ:\n📞 Hotline: {hotline}\n💬 Zalo: {zalo}\nBộ phận tư vấn sẽ báo giá chi tiết theo số lượng anh/chị cần ạ 😊"

👤 Khách: "Có giao hàng tận nơi không?"
🤖 Bot: "Dạ có ạ! BRICON giao hàng toàn quốc 🚚\n• Nội thành TP.HCM: 1-2 ngày\n• Các tỉnh: 2-5 ngày\nAnh/chị ở khu vực nào để em tư vấn thời gian giao hàng cụ thể nhé?"

👤 Khách: "Hôm nay thời tiết thế nào?"
🤖 Bot: "Dạ, em chỉ có thể hỗ trợ về sản phẩm vật liệu xây dựng BRICON thôi ạ 😊 Anh/chị có cần tư vấn về keo dán gạch, keo chà ron hay chống thấm không ạ?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 **BẮT ĐẦU TƯ VẤN NGAY!**
Hãy trả lời khách hàng một cách chuyên nghiệp, thân thiện và hiệu quả nhất!
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
            f"{'👤 Khách hàng' if msg['role'] == 'user' else '🤖 BRICON'}: {msg['content']}"
            for msg in session['chatbot_history'][-5:]
        ])

        # Tạo prompt
        company_info = load_company_info()
        system_prompt = create_system_prompt(company_info)

        full_prompt = f"""{system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📜 **LỊCH SỬ HỘI THOẠI GẦN ĐÂY:**
{history_context if history_context else "(Hội thoại mới)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 **TIN NHẮN MỚI TỪ KHÁCH HÀNG:**
{user_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ **HÃY TRẢ LỜI KHÁCH HÀNG:**
"""

        # Gọi Gemini API
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                    top_p=0.95,
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