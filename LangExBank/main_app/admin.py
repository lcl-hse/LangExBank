import os, time, shutil

from zipfile import ZipFile
from io import BytesIO, StringIO

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
            # load file from form
            path = default_storage.save(
                'data.json',
                ContentFile(request.FILES['datafile'].read())
            )
            path = os.path.join(MEDIA_ROOT, path)
            time.sleep(5)

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
        if "output" in request.GET:
            filename = request.GET["output"]
            if filename:
                # execute command
                os.system(
                    f"python -Xutf8 manage.py dumpdata {request.GET['app_label']} -o {filename} --format {request.GET['format']} --indent {request.GET['indent']}"
                )
                while not os.path.exists(filename):
                    time.sleep(1)

                # read data from file
                data = bytes()
                file_format = str()
                if "zip" in request.GET:
                    # zip output if needed
                    data = BytesIO()
                    zfile = ZipFile(data, 'w')
                    zfile.write(filename)
                    zfile.close()
                    os.remove(filename)
                    filename = f"{filename}.zip"
                    file_format = "zip"
                    data = data.getvalue()
                else:
                    with open(filename, 'rb') as inp:
                        data = inp.read()
                    file_format = request.GET["format"]
                    os.remove(filename)

                # send file with data
                response = HttpResponse(
                    data,
                    content_type=f"application/{file_format}"
                )
                response['Content-Disposition'] = f'attachment; filename = "{filename}"'
                return response

        return render(
            request,
            "admin/dump_data.html",
            extra_context
        )



    def load_mediafiles(self, request, extra_context=None):
        if request.FILES:
            # load zip file from form
            path = default_storage.save(
                'mediafiles.zip',
                ContentFile(request.FILES['datafile'].read())
            )
            path = os.path.join(MEDIA_ROOT, path)
            time.sleep(5)

            # unzip files and move them to mediafiles folder
            # https://stackoverflow.com/a/46954950
            zfile = ZipFile(path)
            for name in zfile.namelist():
                file = zfile.open(name)
                name = os.path.basename(name) # Keep structure with no subfolders in mediafiles
                if name:
                    # filenames must be in UTF-8:
                    with open(
                        os.path.join(MEDIA_ROOT, name),
                        'wb'
                    ) as outp_file:
                        shutil.copyfileobj(file, outp_file)
                file.close()
            zfile.close()
            
            os.remove(path)

            return redirect(
                reverse(
                    "admin:management"
                )
            )
        else:
            return render(
                request,
                "admin/load_mediafiles.html",
                extra_context
            )

    def dump_mediafiles(self, request, extra_context=None):
        if "output" in request.GET:
            filename = request.GET["output"]
            if filename:
                # zip mediafiles
                stream = BytesIO()
                zfile = ZipFile(stream, 'w')
                for root, dirs, files in os.walk(MEDIA_ROOT):
                    for file in files:
                        zfile.write(os.path.join(MEDIA_ROOT, root, file))
                zfile.close()
                # send zipped data
                response = HttpResponse(
                    stream.getvalue(),
                    content_type="application/zip"
                )
                response['Content-Disposition'] = f'attachment; filename = "{filename}"'
                return response
        else:
            return render(
                request,
                "admin/dump_mediafiles.html",
                extra_context
            )

    def random_users(self, request, extra_context=None):
        if request.POST:
            #   -n NUMBER, --number NUMBER
            #                         How many users to create
            #   -r RIGHTS, --rights RIGHTS
            #                         Which type of rights (A - Admin, T - Teacher, S -
            #                         Student) created users should have
            #   -s, --save            Save created user list to a CSV file
            #   -fn FILENAME, --filename FILENAME
            #                         Filename for the saved userlist

            # load data from form
            command_kwargs = {
                'number': int(request.POST['number']),
                'rights': request.POST['rights'],
                'save': bool(request.POST.get('save')),
                'filename': request.POST.get('filename')
            }
            # execute command
            call_command(
                "random_users",
                **command_kwargs
            )
            # send generated file
            if command_kwargs["save"] and command_kwargs["filename"]:
                with open(command_kwargs["filename"], 'rb') as inp:
                    data = inp.read()
                os.remove(command_kwargs["filename"])
                response = HttpResponse(
                    data,
                    content_type="application/json"
                )
                response['Content-Disposition'] = f"attachment; filename = \"{command_kwargs['filename']}\""
                return response
            else:
                return redirect(
                    reverse(
                        "admin:management"
                    )
                )
        if extra_context is None:
            extra_context = {
                "rights": User.rights.field.choices
            }
        return render(
            request,
            "admin/random_users.html",
            extra_context
        )

    def save_right_answers(self, request, extra_context=None):
        if "output" in request.GET:
            #   -q QUIZ, --quiz QUIZ  Id of a quiz
            if request.GET["output"]:
                file = StringIO()
                call_command(
                    "save_right_answers",
                    quiz=request.GET["quiz"],
                    stdout=file
                )
                response = HttpResponse(
                    file.getvalue(),
                    content_type="application/json"
                )
                response['Content-Disposition'] = f"attachment; filename = \"{request.GET['output']}\""
                return response
        if extra_context is None:
            extra_context = {
                "quizzes": Quizz.objects.only("id", "name")
            }
        return render(
            request, 
            "admin/save_right_answers.html",
            extra_context
        )

    def user_info_table(self, request, extra_context=None):
        if request.method == "GET":
            call_command(
                "user_info_table"
            )
            with open("Users.xlsx", 'rb') as inp:
                data = inp.read()
            os.remove("Users.xlsx")
            response = HttpResponse(
                data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename = "Users.xlsx"'
            return response


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
