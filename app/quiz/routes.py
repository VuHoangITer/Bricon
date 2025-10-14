"""
Quiz Routes - Routes cho người dùng làm quiz (KHÔNG CẦN ĐĂNG NHẬP)

Chức năng:
1. Danh sách quiz
2. Bắt đầu làm bài (nhập tên)
3. Làm bài quiz
4. Nộp bài và xem kết quả
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.quiz.models import Quiz, Question, Answer, QuizAttempt, UserAnswer
from datetime import datetime
import random

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')
# ==================== TRANG NHẬP THÔNG TIN TRƯỚC KHI LÀM BÀI ====================
@quiz_bp.route('/<slug>/start', methods=['GET', 'POST'])
def quiz_start(slug):
    """
    Trang nhập thông tin trước khi làm bài
    User nhập tên, email (optional) để bắt đầu
    """
    quiz = Quiz.query.filter_by(slug=slug, is_active=True).first_or_404()

    if request.method == 'POST':
        user_name = request.form.get('user_name', '').strip()
        user_email = request.form.get('user_email', '').strip()
        user_phone = request.form.get('user_phone', '').strip()

        # Validate tên (bắt buộc)
        if not user_name or len(user_name) < 2:
            flash('Vui lòng nhập tên của bạn (ít nhất 2 ký tự)', 'danger')
            return render_template('quiz/quiz_start.html', quiz=quiz)

        # Tạo attempt mới
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_name=user_name,
            user_email=user_email if user_email else None,
            user_phone=user_phone if user_phone else None,
            started_at=datetime.utcnow(),
            total_questions=quiz.questions.count(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )

        db.session.add(attempt)
        db.session.commit()

        # Lưu attempt_id vào session
        session['current_attempt_id'] = attempt.id
        session['quiz_start_time'] = datetime.utcnow().isoformat()

        flash(f'Chào {user_name}! Bắt đầu làm bài "{quiz.title}"', 'success')
        return redirect(url_for('quiz.quiz_take', slug=slug))

    return render_template('quiz/quiz_start.html', quiz=quiz)


# ==================== TRANG LÀM BÀI ====================
@quiz_bp.route('/<slug>/take')
def quiz_take(slug):
    """
    Trang làm bài quiz - Giao diện giống ảnh mẫu
    Hiển thị từng câu hỏi với các đáp án
    """
    quiz = Quiz.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Kiểm tra có attempt trong session không
    attempt_id = session.get('current_attempt_id')
    if not attempt_id:
        flash('Vui lòng nhập thông tin để bắt đầu làm bài!', 'warning')
        return redirect(url_for('quiz.quiz_start', slug=slug))

    attempt = QuizAttempt.query.get(attempt_id)
    if not attempt or attempt.quiz_id != quiz.id:
        flash('Phiên làm bài không hợp lệ!', 'danger')
        session.pop('current_attempt_id', None)
        return redirect(url_for('quiz.quiz_start', slug=slug))

    # Kiểm tra đã hoàn thành chưa
    if attempt.is_completed:
        flash('Bạn đã hoàn thành bài quiz này rồi!', 'info')
        return redirect(url_for('quiz.quiz_result', attempt_id=attempt.id))

    # Lấy danh sách câu hỏi
    questions = quiz.questions.order_by(Question.order).all()

    # Xáo trộn câu hỏi nếu cần
    if quiz.shuffle_questions:
        random.shuffle(questions)

    # Xáo trộn đáp án nếu cần
    for question in questions:
        answers = list(question.answers.order_by(Answer.order).all())
        if quiz.shuffle_answers:
            random.shuffle(answers)
        question.shuffled_answers = answers

    # Lấy các câu đã trả lời (để highlight)
    answered_questions = {ua.question_id for ua in attempt.user_answers.all()}

    # Tính thời gian còn lại
    start_time = datetime.fromisoformat(session.get('quiz_start_time'))
    elapsed_seconds = int((datetime.utcnow() - start_time).total_seconds())
    remaining_seconds = max(0, (quiz.duration_minutes * 60) - elapsed_seconds)

    return render_template('quiz/quiz_take.html',
                           quiz=quiz,
                           attempt=attempt,
                           questions=questions,
                           answered_questions=answered_questions,
                           remaining_seconds=remaining_seconds)


# ==================== LƯU CÂU TRẢ LỜI (AJAX) ====================
@quiz_bp.route('/answer', methods=['POST'])
def save_answer():
    """
    API lưu câu trả lời của user (AJAX)
    Được gọi khi user click vào đáp án
    """
    data = request.get_json()
    attempt_id = session.get('current_attempt_id')

    if not attempt_id:
        return jsonify({'success': False, 'message': 'Phiên làm bài không hợp lệ'}), 400

    attempt = QuizAttempt.query.get(attempt_id)
    if not attempt or attempt.is_completed:
        return jsonify({'success': False, 'message': 'Không thể lưu câu trả lời'}), 400

    question_id = data.get('question_id')
    answer_id = data.get('answer_id')

    if not question_id or not answer_id:
        return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400

    # Kiểm tra question thuộc quiz này không
    question = Question.query.get(question_id)
    if not question or question.quiz_id != attempt.quiz_id:
        return jsonify({'success': False, 'message': 'Câu hỏi không hợp lệ'}), 400

    # Kiểm tra answer thuộc question này không
    answer = Answer.query.get(answer_id)
    if not answer or answer.question_id != question_id:
        return jsonify({'success': False, 'message': 'Đáp án không hợp lệ'}), 400

    # Xóa câu trả lời cũ (nếu có)
    UserAnswer.query.filter_by(
        attempt_id=attempt.id,
        question_id=question_id
    ).delete()

    # Lưu câu trả lời mới
    user_answer = UserAnswer(
        attempt_id=attempt.id,
        question_id=question_id,
        answer_id=answer_id,
        is_correct=answer.is_correct
    )

    db.session.add(user_answer)
    db.session.commit()

    # Đếm số câu đã trả lời
    answered_count = attempt.user_answers.count()
    total_questions = attempt.quiz.questions.count()

    return jsonify({
        'success': True,
        'is_correct': answer.is_correct,
        'answered_count': answered_count,
        'total_questions': total_questions
    })


# ==================== NỘP BÀI ====================
@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    """
    Nộp bài và chuyển đến trang kết quả
    """
    attempt_id = session.get('current_attempt_id')

    if not attempt_id:
        flash('Phiên làm bài không hợp lệ!', 'danger')
        return redirect(url_for('quiz.quiz_list'))

    attempt = QuizAttempt.query.get(attempt_id)
    if not attempt or attempt.is_completed:
        flash('Bài quiz này đã được nộp rồi!', 'info')
        return redirect(url_for('quiz.quiz_result', attempt_id=attempt.id))

    # Tính thời gian làm bài
    start_time = datetime.fromisoformat(session.get('quiz_start_time'))
    time_spent = int((datetime.utcnow() - start_time).total_seconds())

    # Cập nhật attempt
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()
    attempt.time_spent_seconds = time_spent

    # Tính điểm
    attempt.calculate_score()

    # Xóa session
    session.pop('current_attempt_id', None)
    session.pop('quiz_start_time', None)

    db.session.commit()

    flash('Đã nộp bài thành công!', 'success')
    return redirect(url_for('quiz.quiz_result', attempt_id=attempt.id))


# ==================== TRANG KẾT QUẢ ====================
@quiz_bp.route('/result/<int:attempt_id>')
def quiz_result(attempt_id):
    """
    Trang kết quả sau khi nộp bài
    Hiển thị điểm, đáp án đúng/sai
    """
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not attempt.is_completed:
        flash('Bài quiz chưa được hoàn thành!', 'warning')
        return redirect(url_for('quiz.quiz_take', slug=attempt.quiz.slug))

    quiz = attempt.quiz

    # Lấy chi tiết các câu trả lời
    questions_detail = []
    for user_answer in attempt.user_answers.all():
        question = user_answer.question
        selected_answer = user_answer.answer
        correct_answer = question.get_correct_answer()

        questions_detail.append({
            'question': question,
            'selected_answer': selected_answer,
            'correct_answer': correct_answer,
            'is_correct': user_answer.is_correct
        })

    return render_template('quiz/quiz_result.html',
                           attempt=attempt,
                           quiz=quiz,
                           questions_detail=questions_detail)


# ==================== XEM LẠI KẾT QUẢ (PUBLIC) ====================
@quiz_bp.route('/results')
def public_results():
    """
    Trang xem lại kết quả của các lần làm bài (public)
    Search bằng tên hoặc email
    """
    search_query = request.args.get('search', '').strip()

    if not search_query:
        return render_template('quiz/public_results.html', attempts=[])

    # Tìm kiếm theo tên hoặc email
    attempts = QuizAttempt.query.filter(
        QuizAttempt.is_completed == True
    ).filter(
        db.or_(
            QuizAttempt.user_name.ilike(f'%{search_query}%'),
            QuizAttempt.user_email.ilike(f'%{search_query}%')
        )
    ).order_by(QuizAttempt.completed_at.desc()).all()

    return render_template('quiz/public_results.html', attempts=attempts, search_query=search_query)