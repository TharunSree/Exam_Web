# core/management/commands/send_reminders.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import Result

User = get_user_model()

class Command(BaseCommand):
    help = 'Sends email reminders to users who have not taken a quiz in the last 3 days.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to send reminder emails...")

        # Define the inactivity period
        three_days_ago = timezone.now() - timedelta(days=3)

        # Find users who have not taken a quiz recently
        active_users_in_last_3_days = Result.objects.filter(
            completed_at__gte=three_days_ago
        ).values_list('user_id', flat=True).distinct()

        inactive_users = User.objects.exclude(id__in=active_users_in_last_3_days).exclude(is_staff=True)

        email_count = 0
        for user in inactive_users:
            send_mail(
                'Quiz Reminder from Your Self-Generated Exam System',
                f'Hi {user.username},\n\nThis is a friendly reminder that you haven\'t completed a quiz in a few days. Keep up your momentum and take a new quiz today!\n\nBest regards,\nThe Exam System Team',
                'noreply@selfexam.com',
                [user.email],
                fail_silently=False,
            )
            email_count += 1
            self.stdout.write(self.style.SUCCESS(f'Sent reminder to {user.email}'))

        self.stdout.write(self.style.SUCCESS(f'Finished sending emails. Total reminders sent: {email_count}'))