from flask import request, jsonify, session, current_app
from . import chatbot_bp
import google.generativeai as genai
from datetime import datetime
import json
import os

# ==================== GLOBALS ====================
model = None  # Gemini model (per-worker)
_COMPANY_INFO_CACHE = None
_COMPANY_INFO_MTIME = None
_DEFAULT_MODEL_NAME = 'gemini-2.0-flash-lite'

# Từ khoá kích hoạt chế độ "full" (kỹ thuật/CSKH chi tiết)
TECH_KEYWORDS = [
    "thông số", "kỹ thuật", "tds", "định mức", "độ bám", "bám dính",
    "hạn dùng", "hạn sử dụng", "date", "hsd", "đổi trả", "quy cách",
    "màu ron", "màu chà ron", "packaging", "bao bì", "ứng dụng", "hướng dẫn thi công"
]

# ==================== INIT GEMINI ====================
def init_gemini():
    """Khởi tạo Gemini API (được gọi khi app boot và khi lần đầu /send)."""
    global model
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        current_app.logger.warning("⚠️ GEMINI_API_KEY not found in config")
        model = None
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_DEFAULT_MODEL_NAME)
        current_app.logger.info("✅ Gemini API initialized successfully")
    except Exception as e:
        current_app.logger.error(f"❌ Failed to initialize Gemini API: {str(e)}")
        model = None


# ==================== COMPANY INFO (CACHE + INVALIDATION) ====================
def load_company_info():
    """
    Đọc company_info.json với cache theo mtime:
    - Lần đầu: đọc file & cache
    - Khi file đổi (mtime khác): reload
    - Nếu lỗi, trả về cache cũ (nếu có) để không gián đoạn
    """
    global _COMPANY_INFO_CACHE, _COMPANY_INFO_MTIME
    json_path = os.path.join(current_app.root_path, 'chatbot', 'company_info.json')

    try:
        mtime = os.path.getmtime(json_path)
        if _COMPANY_INFO_CACHE is not None and _COMPANY_INFO_MTIME == mtime:
            return _COMPANY_INFO_CACHE

        with open(json_path, 'r', encoding='utf-8') as f:
            _COMPANY_INFO_CACHE = json.load(f)
            _COMPANY_INFO_MTIME = mtime
            current_app.logger.info(f"✅ Loaded company info (mtime={mtime})")
            return _COMPANY_INFO_CACHE
    except FileNotFoundError:
        current_app.logger.error(f"❌ company_info.json not found at {json_path}")
        return _COMPANY_INFO_CACHE or {}
    except json.JSONDecodeError as e:
        current_app.logger.error(f"❌ Invalid JSON: {str(e)}")
        return _COMPANY_INFO_CACHE or {}
    except Exception as e:
        current_app.logger.error(f"❌ load_company_info error: {str(e)}")
        return _COMPANY_INFO_CACHE or {}


# ==================== PROMPT MODES ====================
def pick_mode(user_message: str) -> str:
    """Chọn 'full' nếu có từ khoá kỹ thuật/CSKH sâu; ngược lại 'lite'."""
    low = (user_message or "").lower()
    if any(k in low for k in TECH_KEYWORDS):
        return "full"
    return current_app.config.get("CHATBOT_PROMPT_MODE_DEFAULT", "lite")


def _summarize_products(products, limit=10):
    lines = []
    for p in (products or [])[:limit]:
        name = p.get('name', 'N/A')
        desc = (p.get('description') or '')[:120]
        lines.append(f"• {name}: {desc}")
    return "\n".join(lines)


def _summarize_faq(faq, limit=5, answer_len=150):
    lines = []
    for q in (faq or [])[:limit]:
        lines.append(f"Q: {q.get('question','')}\nA: {(q.get('answer') or '')[:answer_len]}")
    return "\n".join(lines)


def create_prompt(company_info: dict, mode="lite") -> str:
    # Thông tin cơ bản
    company_name = company_info.get('company_name', 'CÔNG TY TNHH BRICON VIỆT NAM')
    contact = company_info.get('contact', {}) or {}
    phone = contact.get('phone', '0901.180.094')
    hotline = contact.get('hotline', '1900 63 62 94')
    email = contact.get('email', 'info@bricon.vn')
    zalo = contact.get('zalo', phone)
    address = contact.get('address', '171 Đường An Phú Đông 03, P. An Phú Đông, Q.12, TP.HCM')
    website = contact.get('website', 'https://www.bricon.vn')
    working_hours = contact.get('working_hours', '8:00 - 17:30 (Thứ 2 - Thứ 7)')

    products = company_info.get('products', []) or []
    faq = company_info.get('faq', []) or []

    if mode == "lite":
        # Gọn nhẹ: tiết kiệm token & cost
        products_summary = _summarize_products(products, limit=10)
        faq_summary = _summarize_faq(faq, limit=5, answer_len=150)

        return f"""BẠN LÀ TRỢ LÝ ẢO {company_name}

📞 LIÊN HỆ: Hotline: {hotline} | Zalo: {zalo} | Email: {email}
📍 Địa chỉ: {address} | 🌐 {website}

📦 SẢN PHẨM CHÍNH:
{products_summary}

❓ FAQ:
{faq_summary}

🎯 NGUYÊN TẮC:
1) Trả lời NGẮN (2–4 câu), đi thẳng trọng tâm
2) KHÔNG đưa giá cụ thể → hướng dẫn liên hệ hotline/Zalo
3) Thân thiện, chuyên nghiệp
4) Không biết thì nói thật và cho thông tin liên hệ

HÃY TRẢ LỜI NGẮN GỌN:"""

    # FULL MODE (giàu thông tin, dựa theo Code 2, nhưng gọn hơn)
    slogan = company_info.get('slogan', 'Kết dính bền lâu – Xây dựng niềm tin')
    branches = contact.get('branches', []) or []
    branches_text = "\n".join([f"• {b.get('name','N/A')}: {b.get('address','N/A')}" for b in branches]) or "—"

    # Sản phẩm chi tiết
    products_list = []
    for p in products:
        info = []
        info.append(f"━━━ {p.get('name','N/A')} ━━━")
        if p.get('category'): info.append(f"• Loại: {p['category']}")
        if p.get('description'): info.append(f"• Mô tả: {p['description']}")
        if p.get('application'):
            info.append("• Ứng dụng:")
            for app in p['application']:
                info.append(f"  - {app}")
        if p.get('technical_specs'):
            info.append("• Thông số kỹ thuật:")
            for k, v in p['technical_specs'].items():
                info.append(f"  - {k}: {v}")
        if p.get('packaging'): info.append(f"• Đóng gói: {p['packaging']}")
        if p.get('colors'): info.append(f"• Màu sắc: {', '.join(p['colors'])}")
        if p.get('expiry'): info.append(f"• Hạn sử dụng: {p['expiry']}")
        products_list.append("\n".join(info))
    products_text = "\n".join(products_list) or "—"

    strengths = company_info.get('strengths', []) or []
    strengths_text = "\n".join([f"✓ {s}" for s in strengths]) or "—"

    rp = company_info.get('return_policy', {}) or {}
    return_summary = rp.get('policy_summary', 'Công ty có chính sách đổi trả linh hoạt')
    conditions = rp.get('conditions', {}) or {}
    conditions_parts = []
    for key, value in conditions.items():
        if isinstance(value, list):
            items = "\n".join([f"  • {item}" for item in value])
            conditions_parts.append(f"\n{key}:\n{items}")
        else:
            conditions_parts.append(f"\n{key}: {value}")
    conditions_text = "".join(conditions_parts)
    notes = rp.get('note', []) or []
    notes_text = "\n".join([f"⚠️ {n}" for n in notes]) if notes else ""

    process = company_info.get('process', []) or []
    process_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(process)]) or "—"

    projects = company_info.get('projects', []) or []
    projects_text = "\n".join([f"• {proj}" for proj in projects[:15]]) or "—"

    company_intro = company_info.get('company_intro', '')
    faq_text = "\n".join([f"❓ {q.get('question','')}\n💡 {q.get('answer','')}\n" for q in faq]) or "—"

    return f"""BẠN LÀ TRỢ LÝ ẢO BRICON - CHUYÊN GIA VẬT LIỆU XÂY DỰNG

🏢 {company_name} | 💡 {slogan}
📞 {hotline} | 💬 Zalo: {zalo} | 📧 {email} | 🌐 {website}
📍 {address} | ⏰ {working_hours}

📖 GIỚI THIỆU:
{company_intro}

— HỆ THỐNG CHI NHÁNH —
{branches_text}

— DANH MỤC SẢN PHẨM CHI TIẾT —
{products_text}

— ƯU ĐIỂM NỔI BẬT —
{strengths_text}

— CHÍNH SÁCH ĐỔI TRẢ —
📌 {return_summary}
✅ Điều kiện:{conditions_text}
{notes_text}

— QUY TRÌNH ĐẶT HÀNG —
{process_text}

— DỰ ÁN TIÊU BIỂU —
{projects_text}

— CÂU HỎI THƯỜNG GẶP —
{faq_text}

🎯 NGUYÊN TẮC TRẢ LỜI:
1) Trả lời TRỰC TIẾP, đúng trọng tâm
2) Không nêu giá; hướng dẫn liên hệ {hotline}/Zalo {zalo}
3) Thân thiện, chuyên nghiệp; chỉ hỏi thêm khi thật sự cần
"""


# ==================== PROMPT BUILDER ====================
def build_full_prompt(system_prompt: str, history_context: str, user_message: str) -> str:
    return f"""{system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📜 LỊCH SỬ HỘI THOẠI:
{history_context if history_context else "(Hội thoại mới)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 TIN NHẮN MỚI:
{user_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ TRẢ LỜI (nhớ quy tắc ở trên):
"""


# ==================== ROUTES ====================
@chatbot_bp.route('/send', methods=['POST'])
def send_message():
    """
    Xử lý tin nhắn:
    - Tuân thủ giới hạn trong app/config.py (15 req/giờ mặc định)
    - Tự động chọn 'lite'/'full' theo intent
    - Timeout gọi model dựa vào GEMINI_TIMEOUT (mặc định 30s) < gunicorn 60s
    """
    global model

    # Bật/tắt chatbot
    if not current_app.config.get('CHATBOT_ENABLED', True):
        return jsonify({'response': '⚠️ Chatbot đang bảo trì. Vui lòng liên hệ: 📞 1900 63 62 94'}), 503

    # Init model nếu chưa có
    if model is None:
        init_gemini()
    if model is None:
        return jsonify({'response': '😔 Chatbot tạm thời không khả dụng.\nLiên hệ: 📞 1900 63 62 94'}), 500

    try:
        data = request.json or {}
        user_message = (data.get('message') or '').strip()

        # Validate
        if not user_message:
            return jsonify({'error': 'Tin nhắn không được để trống'}), 400
        if len(user_message) > 500:
            return jsonify({'error': 'Tin nhắn quá dài (tối đa 500 ký tự)'}), 400

        # Rate limit theo session
        if 'chatbot_request_count' not in session:
            session['chatbot_request_count'] = 0
            session['chatbot_request_start_time'] = datetime.now().timestamp()

        now_ts = datetime.now().timestamp()
        request_limit = int(current_app.config.get('CHATBOT_REQUEST_LIMIT', 15))
        window = int(current_app.config.get('CHATBOT_REQUEST_WINDOW', 3600))  # 1h

        # Reset window
        if now_ts - session['chatbot_request_start_time'] > window:
            session['chatbot_request_count'] = 0
            session['chatbot_request_start_time'] = now_ts

        if session['chatbot_request_count'] >= request_limit:
            return jsonify({
                'response': (
                    f'⏰ Anh/chị đã dùng hết {request_limit} lượt chat/giờ.\n'
                    f'Vui lòng thử lại sau hoặc liên hệ 📞 1900 63 62 94 | Zalo {current_app.config.get("HOTLINE_ZALO","0901.180.094")}'
                )
            })

        session['chatbot_request_count'] += 1

        # Lịch sử hội thoại (giới hạn ngắn để tiết kiệm token)
        history_turns = int(current_app.config.get('CHATBOT_HISTORY_TURNS', 5))
        if 'chatbot_history' not in session:
            session['chatbot_history'] = []
        history_context = "\n".join([
            f"{'Khách' if msg['role']=='user' else 'Bot'}: {msg['content']}"
            for msg in session['chatbot_history'][-history_turns:]
        ])

        # Chọn prompt mode & build prompt
        company_info = load_company_info()
        mode = pick_mode(user_message)  # 'lite' / 'full'
        system_prompt = create_prompt(company_info, mode=mode)
        full_prompt = build_full_prompt(system_prompt, history_context, user_message)

        # Gọi Gemini
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=float(current_app.config.get('CHATBOT_TEMPERATURE', 0.6)),
                    max_output_tokens=int(current_app.config.get('CHATBOT_MAX_OUTPUT_TOKENS', 800 if mode == "full" else 400)),
                    top_p=0.9,
                    top_k=40
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ],
            )
            bot_reply = getattr(response, 'text', '').strip()
            if not bot_reply:
                bot_reply = (
                    "😔 Dạ xin lỗi, em chưa có đủ thông tin để trả lời.\n"
                    "Anh/chị vui lòng liên hệ: 📞 1900 63 62 94 hoặc Zalo 0901.180.094 để được hỗ trợ nhanh ạ."
                )
        except Exception as api_error:
            current_app.logger.error(f"❌ Gemini API error: {str(api_error)}")
            return jsonify({
                'response': '⚠️ Hệ thống đang quá tải, anh/chị vui lòng thử lại sau vài giây hoặc gọi 📞 1900 63 62 94.'
            }), 500

        # Lưu lịch sử (giới hạn 20 message gần nhất)
        session['chatbot_history'].append({'role': 'user', 'content': user_message})
        session['chatbot_history'].append({'role': 'assistant', 'content': bot_reply})
        session['chatbot_history'] = session['chatbot_history'][-20:]
        session.modified = True

        remaining = request_limit - session['chatbot_request_count']

        return jsonify({
            'response': bot_reply,
            'mode': mode,
            'remaining_requests': remaining,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"❌ Chatbot error: {str(e)}", exc_info=True)
        return jsonify({
            'response': '😔 Đã có lỗi xảy ra. Vui lòng liên hệ BRICON: 📞 1900 63 62 94 | Zalo 0901.180.094 | Email info@bricon.vn'
        }), 500


@chatbot_bp.route('/reset', methods=['POST'])
def reset_chat():
    """Xoá lịch sử + đếm lượt"""
    try:
        session.pop('chatbot_history', None)
        session.pop('chatbot_request_count', None)
        session.pop('chatbot_request_start_time', None)
        session.modified = True
        current_app.logger.info("✅ Chat history reset successfully")
        return jsonify({'status': 'success', 'message': '✅ Đã làm mới hội thoại', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        current_app.logger.error(f"❌ Reset chat error: {str(e)}")
        return jsonify({'status': 'error', 'message': '⚠️ Không thể làm mới hội thoại'}), 500


@chatbot_bp.route('/status', methods=['GET'])
def chatbot_status():
    """Kiểm tra trạng thái chatbot"""
    try:
        global model
        limit = int(current_app.config.get('CHATBOT_REQUEST_LIMIT', 15))
        used = int(session.get('chatbot_request_count', 0))
        return jsonify({
            'enabled': current_app.config.get('CHATBOT_ENABLED', True),
            'model_initialized': model is not None,
            'request_limit': limit,
            'remaining_requests': max(0, limit - used),
            'history_length': len(session.get('chatbot_history', [])),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"❌ Status check error: {str(e)}")
        return jsonify({'error': 'Unable to check status'}), 500


# ==================== APP HOOK ====================
def init_chatbot(app):
    """Gọi ở __init__.py khi khởi động app"""
    with app.app_context():
        init_gemini()
        # Preload company info để cache sẵn (không block request đầu)
        try:
            load_company_info()
        except Exception:
            pass
        current_app.logger.info("🤖 BRICON Chatbot initialized (hybrid mode)")
