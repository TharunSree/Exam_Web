# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Add this
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Add this
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='user',
    )


class Exam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    marks_per_correct_answer = models.FloatField(default=4.0)
    negative_marks_per_wrong_answer = models.FloatField(default=1.0)

    def __str__(self):
        return self.name


class Quiz(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    number_of_questions = models.IntegerField(default=10)
    difficulty = models.CharField(max_length=20, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    passage = models.TextField(blank=True, null=True)
    chart_data = models.JSONField(blank=True, null=True)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=10)

    def __str__(self):
        return self.question_text


class Result(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.quiz.title}'


class UserAnswer(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=10,blank=True, null=True)  # e.g., 'option1'
    is_correct = models.BooleanField()

    def __str__(self):
        return f'{self.result.user.username} - {self.question.question_text[:30]}'
