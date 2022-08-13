from django.contrib import admin

# Register your models here.

from .models import User, Student, Quizz, Question, Results, Folder, IELTS_Test, Section, Answer, WrongAnswer, IELTSWritingTask, IELTSWritingResponse


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
admin.site.register(IELTSWritingTask)
admin.site.register(IELTSWritingResponse)

## как вызывать management commands через API
## from djamgo.core.management import call_command
##
## call_command("dumpdata", "<app_label[.ModelName]>", output="<filename>.json")
## call_command("loaddata", "<filename>.json", app="<APP_LABEL>")