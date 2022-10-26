import os, time

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from django.core.management import call_command
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Register your models here.

from main_app.models import User, Student, Quizz, Question, Results
from main_app.models import Folder, IELTS_Test, Section, Answer
from main_app.models import WrongAnswer, IELTSWritingTask, IELTSWritingResponse

from testing_platform.settings import MEDIA_ROOT


class MyAdminSite(admin.AdminSite):
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()

        last_url = urls.pop()
        urls += [
            path(
                "management/",
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

    def management(self, request, extra_context=None):
        return render(
            request,
            "admin/management.html",
            extra_context
        )

    def load_data(self, request, extra_context=None):
        if request.FILES:
            options = {}
            # load file from form
            path = default_storage.save(
                'data.json',
                ContentFile(request.FILES['datafile'].read())
            )
            path = os.path.join(MEDIA_ROOT, path)
            time.sleep(5)
            # insert selected fields from form to options

            print(path)

            # execute command
            call_command(
                "loaddata",
                path
            )
            
            os.remove(path)

            return redirect(
                reverse(
                    "admin:management"
                )
            )
        else:
            return render(
                request,
                "admin/load_data.html",
                extra_context
            )

    def dump_data(self, request, extra_context=None):
        # read form

        # execute command

        # send JSON file with data

        return render(
            request,
            "admin/debug_url.html",
            {"page_name": "dump_data"}
        )

    def load_mediafiles(self, request, extra_context=None):
        # load zip file from form

        # unzip files and move them to mediafiles folder

        raise render(
            request,
            "admin/debug_url.html",
            {"page_name": "load_mediafiles"}
        )

    def dump_mediafiles(self, request, extra_context=None):
        # load zip file from form

        # unzip files and move them to mediafiles folder

        raise render(
            request,
            "admin/debug_url.html",
            {"page_name": "dump_mediafiles"}
        )

    def random_users(self, request, extra_context=None):
        # load data from form

        # execute command

        return render(
            request,
            "admin/debug_url.html",
            {"page_name": "random_users"}
        )
    
    def save_right_answers(self, request, extra_context=None):
        # load data from form

        # execute command

        # send generated file

        return render(
            request, 
            "admin/debug_url.html",
            {"page_name": "save_right_answers"}
        )
    
    def user_info_table(self, request, extra_context=None):
        # load data from form

        # execute command

        # send generated data

        return render(
            request,
            "admin/debug_url.html",
            {"page_name": "user_info_table"}
        )


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
