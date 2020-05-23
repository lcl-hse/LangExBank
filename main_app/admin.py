from django.contrib import admin

# Register your models here.

from .models import User, Student, Quizz, Question, Results, Folder, IELTS_Test, Section, Answer, WrongAnswer


admin.site.register(User)
admin.site.register(Student)
admin.site.register(Quizz)
admin.site.register(Question)
admin.site.register(Results)
admin.site.register(Folder)
admin.site.register(IELTS_Test)
admin.site.register(Section)
admin.site.register(Answer)
admin.site.register(WrongAnswer)