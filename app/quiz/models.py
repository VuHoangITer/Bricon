"""
Quiz Models - Hệ thống kiểm tra kiến thức nhân viên/ứng viên

Bảng:
- Quiz: Đề thi (VD: Python Test Level 1)
- Question: Câu hỏi trong đề
- Answer: Đáp án của câu hỏi (có 1 đáp án đúng)
- QuizAttempt: Lượt làm bài của user
- UserAnswer: Câu trả lời của user trong 1 lần làm bài
"""

from app import db
from datetime import datetime
import json


# ==================== QUIZ MODEL (ĐỀ THI) ====================
class Quiz(db.Model):
    """
    Model Đề thi/kiểm tra
    VD: "Python Basics", "Flask Interview", "SQL Fundamentals"
    """
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # Tên đề thi
    slug = db.Column(db.String(200), unique=True, nullable=False)  # URL-friendly
    description = db.Column(db.Text)  # Mô tả ngắn

    # Cấu hình
    duration_minutes = db.Column(db.Integer, default=30)  # Thời gian làm bài (phút)
    pass_score = db.Column(db.Integer, default=70)  # Điểm đạt (%)
    total_questions = db.Column(db.Integer, default=0)  # Tổng số câu hỏi

    # Cài đặt hiển thị
    show_correct_answers = db.Column(db.Boolean, default=True)  # Hiển thị đáp án sau khi nộp
    shuffle_questions = db.Column(db.Boolean, default=False)  # Xáo trộn câu hỏi
    shuffle_answers = db.Column(db.Boolean, default=True)  # Xáo trộn đáp án

    # Metadata
    category = db.Column(db.String(100))  # Phân loại: "Technical", "HR", "Sales"
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # ==================== ✨ QR_CACHE: Lưu QR Code Cache ====================
    # Tất cả 3 trường này dùng để cache QR code, tránh tạo lại mỗi lần
    qr_code_base64 = db.Column(db.Text, nullable=True)      # Ảnh QR dưới dạng Base64
    quiz_url_cached = db.Column(db.String(500), nullable=True)  # URL đã lưu QR (để phát hiện thay đổi)
    qr_generated_at = db.Column(db.DateTime, nullable=True)  # Thời điểm tạo QR

    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quiz {self.title}>'

    def get_pass_percentage(self):
        """Tính % người đạt"""
        total = self.attempts.filter_by(is_completed=True).count()
        if total == 0:
            return 0
        passed = self.attempts.filter(
            QuizAttempt.is_completed == True,
            QuizAttempt.score >= self.pass_score
        ).count()
        return round((passed / total) * 100, 1)

    def get_average_score(self):
        """Điểm trung bình"""
        attempts = self.attempts.filter_by(is_completed=True).all()
        if not attempts:
            return 0
        return round(sum(a.score for a in attempts) / len(attempts), 1)

    def get_completion_rate(self):
        """Tỷ lệ hoàn thành"""
        total = self.attempts.count()
        if total == 0:
            return 0
        completed = self.attempts.filter_by(is_completed=True).count()
        return round((completed / total) * 100, 1)

    def generate_or_get_qr_code(self, quiz_url):
        """
        ✨ QR_CACHE: Tạo hoặc lấy QR code đã cache
        - Lần đầu: Tạo QR từ URL và lưu vào DB (Base64)
        - Lần sau: Nếu URL không đổi, dùng QR cũ
        - Nếu URL đổi: Tạo QR mới (ví dụ: slug thay đổi)

        Args:
            quiz_url (str): URL đầy đủ của quiz (VD: https://example.com/quiz/python-test)

        Returns:
            str: Base64 string của QR code
        """
        # Nếu URL khác hoặc chưa có QR → tạo cái mới
        if self.quiz_url_cached != quiz_url or not self.qr_code_base64:
            import qrcode
            from io import BytesIO
            import base64

            # Tạo QR code object
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(quiz_url)
            qr.make(fit=True)

            # Convert ảnh sang Base64
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()

            # Lưu vào DB
            self.qr_code_base64 = img_str
            self.quiz_url_cached = quiz_url
            self.qr_generated_at = datetime.utcnow()
            db.session.commit()

        return self.qr_code_base64

    def get_qr_code_data_url(self):
        """
        ✨ QR_CACHE: Trả về data URL để dùng trực tiếp trong <img src="">

        Returns:
            str: Data URL hoặc None nếu chưa có QR
            VD: "data:image/png;base64,iVBORw0KGgoAAAANS..."
        """
        if self.qr_code_base64:
            return f"data:image/png;base64,{self.qr_code_base64}"
        return None


# ==================== QUESTION MODEL (CÂU HỎI) ====================
class Question(db.Model):
    """
    Model Câu hỏi trong đề thi
    Hỗ trợ nhiều loại: Multiple Choice, True/False
    """
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    question_text = db.Column(db.Text, nullable=False)  # Nội dung câu hỏi
    question_type = db.Column(db.String(50), default='multiple_choice')  # 'multiple_choice', 'true_false'

    # Metadata
    order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị
    points = db.Column(db.Integer, default=1)  # Điểm của câu hỏi
    explanation = db.Column(db.Text)  # Giải thích đáp án (optional)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    user_answers = db.relationship('UserAnswer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}>'

    def get_correct_answer(self):
        """Lấy đáp án đúng"""
        return self.answers.filter_by(is_correct=True).first()

    def get_answer_distribution(self):
        """Thống kê % người chọn mỗi đáp án"""
        total = self.user_answers.count()
        if total == 0:
            return {}

        distribution = {}
        for answer in self.answers.all():
            count = self.user_answers.filter_by(answer_id=answer.id).count()
            distribution[answer.answer_text] = round((count / total) * 100, 1)
        return distribution


# ==================== ANSWER MODEL (ĐÁP ÁN) ====================
class Answer(db.Model):
    """
    Model Đáp án cho câu hỏi
    Mỗi câu hỏi có 2-6 đáp án, trong đó 1 đáp án đúng
    """
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)

    answer_text = db.Column(db.Text, nullable=False)  # Nội dung đáp án
    is_correct = db.Column(db.Boolean, default=False)  # Đáp án đúng
    order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Answer {self.id}: {self.answer_text[:30]}>'


# ==================== QUIZ ATTEMPT MODEL (LƯỢT LÀM BÀI) ====================
class QuizAttempt(db.Model):
    """
    Model Lượt làm bài của user
    Không cần đăng nhập - chỉ lưu tên
    """
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    # Thông tin người làm bài (KHÔNG CẦN ĐĂNG NHẬP)
    user_name = db.Column(db.String(200), nullable=False)  # Tên người làm
    user_email = db.Column(db.String(200))  # Email (optional)
    user_phone = db.Column(db.String(20))  # SĐT (optional)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Nếu có tài khoản

    # Trạng thái làm bài
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    time_spent_seconds = db.Column(db.Integer, default=0)  # Thời gian làm bài (giây)

    # Kết quả
    score = db.Column(db.Float, default=0)  # Điểm số (0-100)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)  # Đạt/Không đạt

    # Metadata
    ip_address = db.Column(db.String(50))  # IP của người làm bài
    user_agent = db.Column(db.String(500))  # Browser info

    # Relationships
    user_answers = db.relationship('UserAnswer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<QuizAttempt {self.user_name} - Quiz {self.quiz_id}>'

    def calculate_score(self):
        """Tính điểm cho lượt làm bài"""
        if not self.is_completed:
            return

        quiz = Quiz.query.get(self.quiz_id)
        total_points = sum(q.points for q in quiz.questions.all())

        if total_points == 0:
            self.score = 0
            return

        earned_points = 0
        correct_count = 0
        wrong_count = 0

        for user_answer in self.user_answers.all():
            if user_answer.is_correct:
                earned_points += user_answer.question.points
                correct_count += 1
            else:
                wrong_count += 1

        self.score = round((earned_points / total_points) * 100, 2)
        self.correct_answers = correct_count
        self.wrong_answers = wrong_count
        self.passed = self.score >= quiz.pass_score

        db.session.commit()

    def get_time_spent_formatted(self):
        """Format thời gian làm bài"""
        if not self.time_spent_seconds:
            return "0 phút"

        minutes = self.time_spent_seconds // 60
        seconds = self.time_spent_seconds % 60

        if minutes > 0:
            return f"{minutes} phút {seconds} giây"
        return f"{seconds} giây"


# ==================== USER ANSWER MODEL (CÂU TRẢ LỜI) ====================
class UserAnswer(db.Model):
    """
    Model Câu trả lời của user cho từng câu hỏi
    """
    __tablename__ = 'user_answers'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)

    is_correct = db.Column(db.Boolean, default=False)  # Đúng/Sai
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    answer = db.relationship('Answer', backref='user_answers')

    def __repr__(self):
        return f'<UserAnswer Attempt:{self.attempt_id} Q:{self.question_id}>'