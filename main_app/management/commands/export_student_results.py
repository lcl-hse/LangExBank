import pandas as pd

from main_app.models import *
from django.db.models import Avg, Sum
from django.core.management import BaseCommand



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-avg', '--average', dest='average', action='store_true')
        parser.add_argument('--tests', nargs='+')
        parser.add_argument('--discard', dest='discard', action='store_true')

    def handle(self, *args, **kwargs):
        students = Student.objects.all()

        if 'tests' in kwargs:
            print(f"Extracting data for {(',').join(kwargs['tests'])}")
            tests = IELTS_Test.objects.filter(name__in=kwargs['tests'])
            wtests = IELTSWritingTask.objects.filter(name__in=kwargs['tests'])
        else:
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
        
        if 'discard' in kwargs:
            if kwargs['discard']:
                data = data.dropna(axis=0,
                subset = [col for col in data.columns if col!='Group'],
                how='all')

        data.to_excel('Student_results.xlsx')