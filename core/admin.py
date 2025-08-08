from django.contrib import admin
from .models import CustomUser, Exam, Quiz, Question, Result

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Exam)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Result)