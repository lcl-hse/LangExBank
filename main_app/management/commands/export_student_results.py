import pandas as pd

from main_app.models import *
from django.db.models import Avg, Sum
from django.core.management import BaseCommand



class Command(BaseCommand):
    def add_argument(self, parser):
        parser.add_argument('-avg', '--average', dest='average', action='store_true')
    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        tests = IELTS_Test.objects.all()
        wtests = IELTSWritingTask.objects.all()

        data = []

        for student in students:
            entry = dict()
            entry['student'] = student.login.full_name
            entry['Group'] = student.group

            ## Collecting Reading & Listening tests:
            for test in tests:
                test_results = Results.objects.filter(student=student.login).filter(question__section__ielts_test=test)
                if len(test_results):
                    if kwargs['average']:
                        entry[test.name] = test_results.aggregate(test_grade=Avg('mark'))['test_grade']
                    else:
                        entry[test.name] = test_results.aggregate(test_grade=Sum('mark'))['test_grade']
                else:
                    entry[test.name] = None
            
            ## Collecting Writing tests:
            for wtest in wtests:
                wtest_results = IELTSWritingResponse.objects.filter(student=student.login).filter(task=wtest)
                if len(wtest_results):
                    if kwargs['average']:
                        entry[wtest.name] = wtest_results.aggregate(test_grade=Avg('mark'))['test_grade']
                    else:
                        entry[wtest.name] = wtest_results.aggregate(test_grade=Sum('mark'))['test_grade']
                else:
                    entry[wtest.name] = None
            
            data.append(entry)
        data = pd.DataFrame(data).set_index('student').sort_index(axis=0).sort_index(axis=1)
        data.to_excel('Student_results.xlsx')