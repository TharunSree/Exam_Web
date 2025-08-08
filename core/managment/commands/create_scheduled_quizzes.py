import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Exam, Quiz, Question, Result
from core.ai_utils import generate_quiz_questions

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates scheduled daily and weekend quizzes for active users.'

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

        # Get all non-staff users
        users = User.objects.filter(is_staff=False)

        for user in users:
            # Find the last exam the user took to generate a relevant new quiz
            last_result = Result.objects.filter(user=user).order_by('-completed_at').first()

            if last_result:
                exam_to_use = last_result.quiz.exam
            else:
                # If the user has no history, pick a random exam
                exam_to_use = Exam.objects.order_by('?').first()

            if not exam_to_use:
                self.stdout.write(
                    self.style.WARNING(f"No exams in the database. Cannot create quiz for {user.username}."))
                continue

            self.stdout.write(f"Generating {quiz_type} quiz for {user.username} on {exam_to_use.subject}...")

            # Call our existing AI function
            ai_data = generate_quiz_questions(
                exam_name=exam_to_use.name,
                subject=exam_to_use.subject,
                description=exam_to_use.description,
                num_questions=num_questions,
                difficulty="Medium"  # Scheduled quizzes can have a default difficulty
            )

            if ai_data and 'questions' in ai_data and ai_data['questions']:
                quiz = Quiz.objects.create(
                    user=user,
                    exam=exam_to_use,
                    title=f"{quiz_title_prefix}: {exam_to_use.subject}",
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