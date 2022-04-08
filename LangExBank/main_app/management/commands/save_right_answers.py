from main_app.models import *
from django.core.management.base import BaseCommand

import json

class Command(BaseCommand):
    help = 'Saves right answers for the selected quiz to a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('-q', '--quiz', type=int, help='Id of a quiz')
    
    def handle(self, *args, **kwargs):
        quiz = Quizz.objects.get(id = kwargs['quiz'])
        answers = {'question_'+str(ans.question_id.id): ans.answer_text for ans in Answer.objects.filter(question_id__quiz=quiz)}
        print(json.dumps(answers))