import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Exam, Quiz, Question, Result
from core.ai_utils import generate_quiz_questions

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates scheduled daily and weekend quizzes for active users for each subject they have taken.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Type of quiz to generate ("daily" or "weekend")',
            required=True
        )

    def handle(self, *args, **options):
        quiz_type = options['type']
        if quiz_type not in ['daily', 'weekend']:
            self.stdout.write(self.style.ERROR('Invalid quiz type. Choose "daily" or "weekend".'))
            return

        self.stdout.write(f"Starting to generate {quiz_type} quizzes...")
        
        num_questions = 10 if quiz_type == 'daily' else 25
        quiz_title_prefix = "Daily Challenge" if quiz_type == 'daily' else "Weekend Challenge"

        users = User.objects.filter(is_staff=False)
        
        for user in users:
            # --- New Logic: Find all unique exams the user has ever taken ---
            past_exam_ids = Result.objects.filter(user=user).values_list('quiz__exam_id', flat=True).distinct()
            
            if not past_exam_ids:
                self.stdout.write(self.style.WARNING(f"User {user.username} has no quiz history. Skipping."))
                continue

            exams_to_generate = Exam.objects.filter(id__in=past_exam_ids)
            self.stdout.write(f"Found {exams_to_generate.count()} unique subjects for {user.username}.")

            # --- Loop through each subject and create a quiz ---
            for exam in exams_to_generate:
                self.stdout.write(f"Generating {quiz_type} quiz for {user.username} on {exam.subject}...")

                # Prevent creating a duplicate daily/weekend quiz if one already exists for today
                today = timezone.now().date()
                if Quiz.objects.filter(user=user, exam=exam, title__startswith=quiz_title_prefix, created_at__date=today).exists():
                    self.stdout.write(self.style.WARNING(f"A {quiz_type} quiz for {exam.subject} already exists today for {user.username}. Skipping."))
                    continue

                ai_data = generate_quiz_questions(
                    exam_name=exam.name,
                    subject=exam.subject,
                    description=exam.description,
                    num_questions=num_questions,
                    difficulty="Medium"
                )

                if ai_data and 'questions' in ai_data and ai_data['questions']:
                    quiz = Quiz.objects.create(
                        user=user,
                        exam=exam,
                        title=f"{quiz_title_prefix}: {exam.subject}",
                        number_of_questions=len(ai_data['questions']),
                        difficulty="Medium"
                    )

                    passage_text = ai_data.get('passage')
                    chart_data_json = ai_data.get('chart_data')

                    for q_data in ai_data['questions']:
                        Question.objects.create(
                            quiz=quiz,
                            passage=passage_text,
                            chart_data=chart_data_json,
                            question_text=q_data.get('question_text', ''),
                            option1=q_data.get('option1', ''),
                            option2=q_data.get('option2', ''),
                            option3=q_data.get('option3', ''),
                            option4=q_data.get('option4', ''),
                            correct_option=q_data.get('correct_option', '')
                        )
                    self.stdout.write(self.style.SUCCESS(f"Successfully created quiz for {user.username}."))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to generate quiz from AI for {user.username}."))

        self.stdout.write(self.style.SUCCESS("Finished generating all scheduled quizzes."))
