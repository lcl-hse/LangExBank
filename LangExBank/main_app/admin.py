from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Register your models here.

from .models import User, Student, Quizz, Question, Results, Folder, IELTS_Test, Section, Answer, WrongAnswer, IELTSWritingTask, IELTSWritingResponse


class MyAdminSite(admin.AdminSite):
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()

        # подсовываем в urls новую главную страницу
        urls[0] = [
            path('^$', self.admin_view(self.index))
        ]

        urls += [
            path('my_view/', self.admin_view(self.my_view))
        ]
        return urls
    
    # view новой главной страницы
    def index(self):
        return render("admin_index.html")

    def my_view(self, request):
        return HttpResponse("Hello!")

admin_site = MyAdminSite()

admin_site.register(User)
admin_site.register(Student)
admin_site.register(Quizz)
admin_site.register(Question)
admin_site.register(Results)
admin_site.register(Folder)
admin_site.register(IELTS_Test)
admin_site.register(Section)
admin_site.register(Answer)
admin_site.register(WrongAnswer)
admin_site.register(IELTSWritingTask)
admin_site.register(IELTSWritingResponse)

# admin.site.register(User)
# admin.site.register(Student)
# admin.site.register(Quizz)
# admin.site.register(Question)
# admin.site.register(Results)
# admin.site.register(Folder)
# admin.site.register(IELTS_Test)
# admin.site.register(Section)
# admin.site.register(Answer)
# admin.site.register(WrongAnswer)
# admin.site.register(IELTSWritingTask)
# admin.site.register(IELTSWritingResponse)

## как вызывать management commands через API
## from djamgo.core.management import call_command
##
## call_command("dumpdata", "<app_label[.ModelName]>", output="<filename>.json")
## call_command("loaddata", "<filename>.json", app="<APP_LABEL>")