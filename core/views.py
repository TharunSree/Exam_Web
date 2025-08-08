from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q

from .models import Exam, Quiz, Question, Result, UserAnswer
from .ai_utils import generate_quiz_questions


@login_required
def dashboard_view(request):
    """
    Renders the main dashboard, fetching exams and recent quiz results.
    """
    exams = Exam.objects.all().order_by('name', 'subject')
    recent_results = Result.objects.filter(user=request.user).order_by('-completed_at')[:5]

    context = {
        'user': request.user,
        'exams': exams,
        'recent_results': recent_results,
    }
    return render(request, 'dashboard.html', context)


@login_required
def generate_quiz_view(request):
    """
    Generates a new quiz, handling adaptive difficulty and structured JSON from the AI.
    """
    if request.method == 'POST':
        custom_material_text = None
        try:
            exam_id = request.POST.get('exam')
            num_questions = int(request.POST.get('num_questions', 10))
            exam = get_object_or_404(Exam, id=exam_id)
            
            if 'study_material' in request.FILES:
                uploaded_file = request.FILES['study_material']
                # For simplicity, we'll read it as text. Ensure it's not too large.
                if uploaded_file.size > 5_000_000:  # Limit to 5MB
                    messages.error(request, "Uploaded file is too large (max 5MB).")
                    return redirect('dashboard')
                # Read the content of the uploaded file
                custom_material_text = uploaded_file.read().decode('utf-8')

            # --- Adaptive Difficulty Logic ---
            last_three_results = Result.objects.filter(user=request.user, quiz__exam=exam).order_by('-completed_at')[:3]
            difficulty = "Medium"
            if last_three_results.count() >= 3:
                average_score = last_three_results.aggregate(Avg('score'))['score__avg']
                if average_score > 75:
                    difficulty = "Hard"
                elif average_score < 40:
                    difficulty = "Easy"

            # Call the AI utility
            ai_data = generate_quiz_questions(
                exam.name,
                exam.subject,
                exam.description,
                num_questions,
                difficulty,
                custom_material=custom_material_text
            )

            # Check for a valid AI response
            if ai_data and 'questions' in ai_data and ai_data['questions']:
                quiz_title = f'{exam.subject} Quiz ({difficulty})'
                quiz = Quiz.objects.create(
                    user=request.user,
                    exam=exam,
                    title=quiz_title,
                    difficulty=difficulty,
                    number_of_questions=len(ai_data['questions'])
                )

                passage_text = ai_data.get('passage')
                chart_data_json = ai_data.get('chart_data')

                # Create questions from the AI data
                for q_data in ai_data['questions']:
                    Question.objects.create(
                        quiz=quiz,
                        passage=passage_text,
                        chart_data=chart_data_json,
                        question_text=q_data.get('question_text', 'No text provided'),
                        option1=q_data.get('option1', ''),
                        option2=q_data.get('option2', ''),
                        option3=q_data.get('option3', ''),
                        option4=q_data.get('option4', ''),
                        correct_option=q_data.get('correct_option', '')
                    )

                messages.success(request, f'Successfully generated a new quiz for {exam.name}!')
                return redirect('take_quiz', quiz_id=quiz.id)
            else:
                messages.error(request, 'The AI response was invalid or contained no questions. Please try again.')

        except Exception as e:
            messages.error(request, f'An unexpected error occurred during quiz generation: {e}')

    return redirect('dashboard')


# In core/views.py

@login_required
def take_quiz_view(request, quiz_id):
    """
    Displays a quiz and processes the submission with correct handling
    for unanswered questions.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        correct_answers_count = 0
        wrong_answers_count = 0  # This will now only count explicitly wrong answers

        result = Result.objects.create(user=request.user, quiz=quiz, score=0)

        # Loop through every question in the quiz to check its status
        for question in quiz.questions.all():
            selected_option = request.POST.get(f'question_{question.id}')

            # This is the key change: Check if the question was answered
            if selected_option:
                # The question was answered, now check if it's correct
                is_correct = (selected_option == question.correct_option)
                if is_correct:
                    correct_answers_count += 1
                else:
                    wrong_answers_count += 1  # Penalize only if it's explicitly wrong
            else:
                # The question was not answered, so it is neither correct nor incorrect
                is_correct = False  # Mark it as not correct for review purposes

            # Save the user's answer (or lack thereof) for review
            UserAnswer.objects.create(
                result=result,
                question=question,
                selected_option=selected_option,  # This will be None if unanswered
                is_correct=is_correct
            )

        # --- New Scoring Logic ---
        # The calculation now correctly ignores unanswered questions for negative marking
        exam = quiz.exam
        total_score = (correct_answers_count * exam.marks_per_correct_answer) - (
                wrong_answers_count * exam.negative_marks_per_wrong_answer)

        result.score = total_score
        result.save()

        return redirect('quiz_result', result_id=result.id)

    context = {'quiz': quiz}
    return render(request, 'quiz_take.html', context)


@login_required
def weekly_report_view(request):
    """
    Generates and displays a performance report for the last 7 days.
    """
    user = request.user
    one_week_ago = timezone.now() - timedelta(days=7)

    # Get all results from the last week
    recent_results = Result.objects.filter(user=user, completed_at__gte=one_week_ago)

    if not recent_results.exists():
        # Handle case where there's no recent activity
        return render(request, 'weekly_report.html', {'no_data': True})

    # Calculate overall stats
    total_quizzes = recent_results.count()
    overall_avg_score = recent_results.aggregate(Avg('score'))['score__avg']

    # Calculate performance by subject
    subject_performance = recent_results.values(
        'quiz__exam__subject'
    ).annotate(
        average_score=Avg('score'),
        quizzes_taken=Count('id')
    ).order_by('-average_score')

    best_subject = subject_performance.first()
    worst_subject = subject_performance.last()

    # Data for the performance over time chart
    performance_over_time = recent_results.order_by('completed_at').values('completed_at__date', 'score')

    chart_labels = [entry['completed_at__date'].strftime('%b %d') for entry in performance_over_time]
    chart_data = [round(entry['score'], 2) for entry in performance_over_time]

    # ApexCharts configuration for the line chart
    performance_chart_options = {
        "chart": {"type": "line", "height": 350, "toolbar": {"show": False}},
        "series": [{"name": "Score", "data": chart_data}],
        "xaxis": {"categories": chart_labels},
        "stroke": {"curve": "smooth", "width": 2},
        "colors": ["#604ae3"],
        "markers": {"size": 4}
    }

    context = {
        'total_quizzes': total_quizzes,
        'overall_avg_score': overall_avg_score,
        'best_subject': best_subject,
        'worst_subject': worst_subject,
        'subject_performance': subject_performance,
        'performance_chart_options': performance_chart_options,
    }
    return render(request, 'weekly_reports.html', context)


@login_required
def quiz_result_view(request, result_id):
    """
    Displays the result of a completed quiz.
    """
    result = get_object_or_404(Result, id=result_id, user=request.user)
    context = {'result': result}
    return render(request, 'quiz_result.html', context)


@login_required
def quiz_review_view(request, result_id):
    """
    Displays a detailed review of a completed quiz's answers.
    """
    result = get_object_or_404(Result, id=result_id, user=request.user)
    context = {'result': result}
    return render(request, 'quiz_review.html', context)


@login_required
def quiz_history_view(request):
    """
    Displays a complete history of all quizzes taken by the user.
    """
    all_results = Result.objects.filter(user=request.user).order_by('-completed_at')
    context = {'all_results': all_results}
    return render(request, 'quiz_history.html', context)


def logout_view(request):
    """
    Logs the user out.
    """
    logout(request)
    return redirect('login')
