from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.core.management import call_command

# Register your models here.

from .models import User, Student, Quizz, Question, Results, Folder, IELTS_Test, Section, Answer, WrongAnswer, IELTSWritingTask, IELTSWritingResponse


class MyAdminSite(admin.AdminSite):
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()

        last_url = urls.pop()
        urls += [
            # path(
            #     'my_view/',
            #     self.admin_view(self.my_view),
            #     name="my_view"
            # ),
            path(
                'management/',
                self.admin_view(self.management),
                name="management"
            ),
            path(
                "management/load_data/",
                self.admin_view(self.load_data),
                name="load_data"
            ),
            path(
                "management/dump_data/",
                self.admin_view(self.dump_data),
                name="dump_data"
            ),
            path(
                "management/load_mediafiles/",
                self.admin_view(self.load_mediafiles),
                name="load_mediafiles"
            ),
            path(
                "management/dump_mediafiles/",
                self.admin_view(self.dump_mediafiles),
                name="dump_mediafiles"
            ),
            path(
                "management/random_users/",
                self.admin_view(self.random_users),
                name="random_users"
            ),
            path(
                "management/save_right_answers/",
                self.admin_view(self.save_right_answers),
                name="save_right_answers"
            ),
            path(
                "management/user_info_table/",
                self.admin_view(self.user_info_table),
                name="user_info_table"
            ),
            last_url
        ]

        return urls

    # def my_view(self, request, extra_context=None):
    #     return HttpResponse("Hello!")
    
    def management(self, request, extra_context=None):
        return render(request, "admin/management.html")

    def load_data(self, request, extra_context=None):
        # load file from form

        # execute command

        return render(request, "admin/debug_url.html", {"page_name": "load_data"})

    def dump_data(self, request, extra_context=None):
        # read form

        # execute command

        # send JSON file with data

        return render(request, "admin/debug_url.html", {"page_name": "dump_data"})

    def load_mediafiles(self, request, extra_context=None):
        # load zip file from form

        # unzip files and move them to mediafiles folder

        raise render(request, "admin/debug_url.html", {"page_name": "load_mediafiles"})

    def dump_mediafiles(self, request, extra_context=None):
        # load zip file from form

        # unzip files and move them to mediafiles folder

        raise render(request, "admin/debug_url.html", {"page_name": "dump_mediafiles"})

    def random_users(self, request, extra_context=None):
        # load data from form

        # execute command

        return render(request, "admin/debug_url.html", {"page_name": "random_users"})
    
    def save_right_answers(self, request, extra_context=None):
        # load data from form

        # execute command

        # send generated file

        return render(request, "admin/debug_url.html", {"page_name": "save_right_answers"})
    
    def user_info_table(self, request, extra_context=None):
        # load data from form

        # execute command

        # send generated data

        return render(request, "admin/debug_url.html", {"page_name": "user_info_table"})


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