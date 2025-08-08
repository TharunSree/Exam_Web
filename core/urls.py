# core/urls.py

from django.urls import path
from django.contrib.auth.views import LoginView
from .views import *

urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('', dashboard_view, name='home'),  # Redirect empty path to dashboard
    path('generate-quiz/', generate_quiz_view, name='generate_quiz'),
    path('take-quiz/<int:quiz_id>/', take_quiz_view, name='take_quiz'),
    path('result/<int:result_id>/', quiz_result_view, name='quiz_result'),
    path('history/', quiz_history_view, name='quiz_history'),
    path('review/<int:result_id>/', quiz_review_view, name='quiz_review'),
    path('history/', quiz_history_view, name='quiz_history'),
    path('report/', weekly_report_view, name='weekly_report'),
]
