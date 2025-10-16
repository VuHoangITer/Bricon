"""
Quiz Admin Routes - CRUD cho Admin quản lý Quiz

Chức năng:
1. Quản lý Quiz (CRUD)
2. Quản lý Question & Answer (CRUD)
3. Xem kết quả của ứng viên
4. Thống kê chi tiết

Yêu cầu: Login và có quyền manage_quiz
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.quiz.models import Quiz, Question, Answer, QuizAttempt, UserAnswer
from app.decorators import permission_required
from datetime import datetime
from sqlalchemy import func

quiz_admin_bp = Blueprint('quiz_admin', __name__, url_prefix='/admin/quiz')


# ==================== QUẢN LÝ QUIZ ====================

# ✨ QR_CACHE: Thay thế hàm quizzes() hoàn toàn (từ dòng @quiz_admin_bp.route('/quizzes'))

@quiz_admin_bp.route('/quizzes')
@permission_required('manage_quiz')
def quizzes():
    """
    ✨ QR_CACHE: Danh sách tất cả quiz + Generate QR code cache
    """
    page = request.args.get('page', 1, type=int)
    # ✨ QR_CACHE: Thêm search filter
    search = request.args.get('search', '').strip()

    # ✨ QR_CACHE: Lọc theo search nếu có
    query = Quiz.query
    if search:
        query = query.filter(Quiz.title.ilike(f'%{search}%'))

    quizzes = query.order_by(Quiz.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Thống kê cho mỗi quiz
    quiz_stats = []
    for quiz in quizzes.items:
        # ✨ QR_CACHE: QUAN TRỌNG - Tạo/Update QR code cache tại đây
        # Chỉ tạo 1 lần hoặc khi URL thay đổi
        from flask import url_for
        quiz_url = url_for('quiz.quiz_take', slug=quiz.slug, _external=True)
        quiz.generate_or_get_qr_code(quiz_url)

        stats = {
            'quiz': quiz,
            'total_questions': quiz.questions.count(),
            'total_attempts': quiz.attempts.count(),
            'completed_attempts': quiz.attempts.filter_by(is_completed=True).count(),
            'pass_rate': quiz.get_pass_percentage(),
            'avg_score': quiz.get_average_score()
        }
        quiz_stats.append(stats)

    return render_template('admin/quiz/quizzes.html',
                           quizzes=quizzes,
                           quiz_stats=quiz_stats)


# ✨ QR_CACHE: Sửa hàm add_quiz - tạo QR khi thêm quiz mới
@quiz_admin_bp.route('/quizzes/add', methods=['GET', 'POST'])
@permission_required('manage_quiz')
def add_quiz():
    """✨ QR_CACHE: Thêm quiz mới + Generate QR ngay"""
    from app.forms import QuizForm
    form = QuizForm()

    if form.validate_on_submit():
        from app.utils import slugify
        from flask import url_for

        quiz = Quiz(
            title=form.title.data,
            slug=form.slug.data or slugify(form.title.data),
            description=form.description.data,
            duration_minutes=form.duration_minutes.data,
            pass_score=form.pass_score.data,
            show_correct_answers=form.show_correct_answers.data,
            shuffle_questions=form.shuffle_questions.data,
            shuffle_answers=form.shuffle_answers.data,
            category=form.category.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )

        db.session.add(quiz)
        db.session.commit()

        # ✨ QR_CACHE: Tạo QR code ngay sau khi tạo quiz
        quiz_url = url_for('quiz.quiz_take', slug=quiz.slug, _external=True)
        quiz.generate_or_get_qr_code(quiz_url)

        flash(f'✅ Đã tạo quiz "{quiz.title}" thành công!', 'success')
        return redirect(url_for('quiz_admin.edit_questions', quiz_id=quiz.id))

    return render_template('admin/quiz/quiz_form.html', form=form, title='Thêm Quiz')


# ✨ QR_CACHE: Sửa hàm edit_quiz - update QR nếu slug thay đổi
@quiz_admin_bp.route('/quizzes/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('manage_quiz')
def edit_quiz(id):
    """✨ QR_CACHE: Sửa quiz + Regenerate QR nếu slug thay đổi"""
    from app.forms import QuizForm
    from flask import url_for

    quiz = Quiz.query.get_or_404(id)
    form = QuizForm(obj=quiz)

    if form.validate_on_submit():
        quiz.title = form.title.data
        quiz.slug = form.slug.data
        quiz.description = form.description.data
        quiz.duration_minutes = form.duration_minutes.data
        quiz.pass_score = form.pass_score.data
        quiz.show_correct_answers = form.show_correct_answers.data
        quiz.shuffle_questions = form.shuffle_questions.data
        quiz.shuffle_answers = form.shuffle_answers.data
        quiz.category = form.category.data
        quiz.is_active = form.is_active.data

        db.session.commit()

        # ✨ QR_CACHE: Nếu slug thay đổi, regenerate QR code
        quiz_url = url_for('quiz.quiz_take', slug=quiz.slug, _external=True)
        quiz.generate_or_get_qr_code(quiz_url)

        flash('✅ Đã cập nhật quiz thành công!', 'success')
        return redirect(url_for('quiz_admin.quizzes'))

    return render_template('admin/quiz/quiz_form.html',
                           form=form,
                           quiz=quiz,
                           title=f'Sửa Quiz: {quiz.title}')


@quiz_admin_bp.route('/quizzes/delete/<int:id>')
@permission_required('manage_quiz')
def delete_quiz(id):
    """Xóa quiz"""
    quiz = Quiz.query.get_or_404(id)

    # Kiểm tra có attempt nào chưa
    if quiz.attempts.count() > 0:
        flash('⚠️ Không thể xóa quiz đã có người làm bài! Hãy vô hiệu hóa thay vì xóa.', 'warning')
        return redirect(url_for('quiz_admin.quizzes'))

    db.session.delete(quiz)
    db.session.commit()

    flash('✅ Đã xóa quiz thành công!', 'success')
    return redirect(url_for('quiz_admin.quizzes'))


# ==================== QUẢN LÝ QUESTIONS & ANSWERS ====================

@quiz_admin_bp.route('/quizzes/<int:quiz_id>/questions', methods=['GET', 'POST'])
@permission_required('manage_quiz')
def edit_questions(quiz_id):
    """
    Trang quản lý câu hỏi của 1 quiz
    Hiển thị toàn bộ câu hỏi (KHÔNG PHÂN TRANG)
    """
    quiz = Quiz.query.get_or_404(quiz_id)

    # Lấy tất cả câu hỏi, sắp xếp theo thứ tự
    questions = Question.query.filter_by(quiz_id=quiz_id)\
        .order_by(Question.order.asc()).all()

    return render_template(
        'admin/quiz/questions.html',
        quiz=quiz,
        questions=questions
    )



@quiz_admin_bp.route('/questions/add', methods=['POST'])
@permission_required('manage_quiz')
def add_question():
    print("=== DEBUG FORM DATA ===")
    print(request.form)
    """Thêm câu hỏi từ form thủ công"""
    quiz_id = request.form.get('quiz_id')
    question_text = request.form.get('question_text')
    question_type = request.form.get('question_type', 'multiple_choice')
    points = int(request.form.get('points', 1))
    explanation = request.form.get('explanation')

    # Kiểm tra dữ liệu tối thiểu
    if not quiz_id or not question_text or len(question_text.strip()) < 1:
        flash('❌ Dữ liệu không hợp lệ (thiếu quiz_id hoặc nội dung câu hỏi)!', 'danger')
        return redirect(url_for('quiz_admin.edit_questions', quiz_id=quiz_id))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash('❌ Quiz không tồn tại!', 'danger')
        return redirect(url_for('quiz_admin.quizzes'))

    # Tạo câu hỏi
    question = Question(
        quiz_id=quiz.id,
        question_text=question_text.strip(),
        question_type=question_type,
        points=points,
        explanation=explanation,
        order=quiz.questions.count() + 1
    )
    db.session.add(question)
    db.session.flush()

    # Lấy danh sách đáp án
    answers_data = request.form.getlist('answers[]')
    correct_index = int(request.form.get('correct_answer', 0))

    for idx, text in enumerate(answers_data):
        if text.strip():
            db.session.add(Answer(
                question_id=question.id,
                answer_text=text.strip(),
                is_correct=(idx == correct_index),
                order=idx
            ))

    # Cập nhật tổng số câu hỏi
    quiz.total_questions = quiz.questions.count()
    db.session.commit()

    flash('✅ Đã thêm câu hỏi thành công!', 'success')
    return redirect(url_for('quiz_admin.edit_questions', quiz_id=quiz.id))


@quiz_admin_bp.route('/questions/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('manage_quiz')
def edit_question(id):
    """Sửa câu hỏi - Xóa user_answers nếu cần"""
    question = Question.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            question.question_text = request.form.get('question_text', '').strip()
            question.explanation = request.form.get('explanation', '')
            question.points = int(request.form.get('points', 1))

            if not question.question_text:
                flash('❌ Nội dung câu hỏi không được để trống!', 'danger')
                return redirect(url_for('quiz_admin.edit_question', id=id))

            correct_index = int(request.form.get('correct_answer', 0))
            answers_data = request.form.getlist('answers[]')

            valid_answers = [a.strip() for a in answers_data if a.strip()]
            if len(valid_answers) < 2:
                flash('❌ Phải có ít nhất 2 đáp án!', 'danger')
                return redirect(url_for('quiz_admin.edit_question', id=id))

            # ✅ XÓA USER_ANSWERS TRƯỚC (nếu có)
            UserAnswer.query.filter_by(question_id=question.id).delete()

            # Sau đó xóa answers cũ
            Answer.query.filter_by(question_id=question.id).delete()

            # Tạo answers mới
            for idx, text in enumerate(answers_data):
                if text.strip():
                    answer = Answer(
                        question_id=question.id,
                        answer_text=text.strip(),
                        is_correct=(idx == correct_index),
                        order=idx
                    )
                    db.session.add(answer)

            db.session.commit()
            flash('✅ Đã cập nhật câu hỏi thành công!', 'success')
            return redirect(url_for('quiz_admin.edit_questions', quiz_id=question.quiz_id))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Lỗi: {str(e)}', 'danger')
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    answers = question.answers.order_by(Answer.order).all()
    return render_template('admin/quiz/question_form.html',
                           question=question,
                           answers=answers)


@quiz_admin_bp.route('/questions/delete/<int:id>')
@permission_required('manage_quiz')
def delete_question(id):
    """Xóa câu hỏi"""
    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id

    db.session.delete(question)

    # Cập nhật lại total_questions
    quiz = Quiz.query.get(quiz_id)
    quiz.total_questions = quiz.questions.count()

    db.session.commit()

    flash('✅ Đã xóa câu hỏi thành công!', 'success')
    return redirect(url_for('quiz_admin.edit_questions', quiz_id=quiz_id))


# ==================== XEM KẾT QUẢ CỦA ỨNG VIÊN ====================

@quiz_admin_bp.route('/results')
@permission_required('manage_quiz')
def results():
    """
    Xem tất cả kết quả làm bài
    Filter theo quiz, tên, điểm
    """
    page = request.args.get('page', 1, type=int)
    quiz_id = request.args.get('quiz_id', type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')  # 'passed', 'failed'

    query = QuizAttempt.query.filter_by(is_completed=True)

    if quiz_id:
        query = query.filter_by(quiz_id=quiz_id)

    if search:
        query = query.filter(
            db.or_(
                QuizAttempt.user_name.ilike(f'%{search}%'),
                QuizAttempt.user_email.ilike(f'%{search}%')
            )
        )

    if status == 'passed':
        query = query.filter_by(passed=True)
    elif status == 'failed':
        query = query.filter_by(passed=False)

    attempts = query.order_by(QuizAttempt.completed_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )

    quizzes = Quiz.query.filter_by(is_active=True).all()

    return render_template('admin/quiz/results.html',
                           attempts=attempts,
                           quizzes=quizzes)


@quiz_admin_bp.route('/results/<int:attempt_id>')
@permission_required('manage_quiz')
def view_result(attempt_id):
    """Xem chi tiết kết quả của 1 lượt làm bài"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    # Lấy chi tiết từng câu trả lời
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

    return render_template('admin/quiz/result_detail.html',
                           attempt=attempt,
                           questions_detail=questions_detail)

# ==================== XOÁ KẾT QUẢ ỨNG VIÊN ====================
@quiz_admin_bp.route('/results/<int:attempt_id>/delete', methods=['POST'])
def delete_attempt(attempt_id):
    """Xóa kết quả làm bài (QuizAttempt)"""
    from app.quiz.models import QuizAttempt, UserAnswer
    from app import db

    attempt = QuizAttempt.query.get_or_404(attempt_id)

    # Xoá tất cả câu trả lời liên quan
    UserAnswer.query.filter_by(attempt_id=attempt.id).delete()

    # Xoá chính lượt làm bài
    db.session.delete(attempt)
    db.session.commit()

    flash(f'✅ Đã xóa kết quả của "{attempt.user_name}"', 'success')
    return redirect(url_for('quiz_admin.results'))



# ==================== THỐNG KÊ CHI TIẾT ====================

@quiz_admin_bp.route('/statistics')
@permission_required('manage_quiz')
def statistics():
    """
    Trang thống kê tổng quan hệ thống quiz
    - Tổng quiz, câu hỏi, lượt làm bài
    - Top quiz phổ biến
    - Tỷ lệ đạt/không đạt
    """
    total_quizzes = Quiz.query.count()
    total_questions = Question.query.count()
    total_attempts = QuizAttempt.query.filter_by(is_completed=True).count()

    # Top quiz có nhiều người làm nhất
    top_quizzes = db.session.query(
        Quiz.title,
        func.count(QuizAttempt.id).label('attempt_count')
    ).join(QuizAttempt).filter(
        QuizAttempt.is_completed == True
    ).group_by(Quiz.id).order_by(
        func.count(QuizAttempt.id).desc()
    ).limit(5).all()

    # Thống kê đạt/không đạt
    passed_count = QuizAttempt.query.filter_by(is_completed=True, passed=True).count()
    failed_count = QuizAttempt.query.filter_by(is_completed=True, passed=False).count()

    return render_template('admin/quiz/statistics.html',
                           total_quizzes=total_quizzes,
                           total_questions=total_questions,
                           total_attempts=total_attempts,
                           top_quizzes=top_quizzes,
                           passed_count=passed_count,
                           failed_count=failed_count)
