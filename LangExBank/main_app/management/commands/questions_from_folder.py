from main_app.models import *
from django.core.management.base import BaseCommand
from testmaker import testmaker
from DisGen.distractor_generator import get_distractors
from main_app.utils import get_distractors_from_disselector

import time
import json
import re

import pandas as pd


class Command(BaseCommand):
    help = 'Fills database with questions generated from error annotations of texts'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--folder', type=str, help='Folder to process')
        parser.add_argument('-t', '--tag', nargs='+', type=str, help='Error tag to include')
        parser.add_argument('-s', '--strike', dest='strike', action='store_true', help='Whether to strike out wrong answers')
        parser.add_argument('-m', '--multchoice', dest='mult_choice', action='store_true', help='Whether to make generated questions multiple choice')

    def handle(self, *args, **kwargs):
        ## To add: check for duplicate documents:
        generate_questions(kwargs['folder'], kwargs['tag'], kwargs['strike'])


def generate_questions(folder, tags, strike, delete_downloaded=True,
                       new_qfolder=False, qfolder_name=None, ukey_prefix='',
                       multiple_choice=False, filter_query=None, context=False,
                       distractor_model=None):
    exercises = testmaker.download_folder_and_make_exercises(folder_name=folder,
    error_types=tags, file_output=False, moodle_output=False, make_two_variants=False,
    delete_downloaded=delete_downloaded, filter_query=filter_query, context=context)['short_answer']
    last = Question.objects.last()

    # Исправить, не доставать id эскплицитно
    # а доставать по ukey
    # if last is not None:
    #     last_id = last.id
    # else:
    #     last_id = -1

    ukey = ukey_prefix + "_" + str(time.time())

    if multiple_choice:
        if distractor_model == 'disgen':
            data = [(i[0], i[1][0], i[3], i[4]['folder'], i[4]['filename']) for i in exercises]
            data = pd.DataFrame(data,
                                columns=['Sentence', 'Right answer', 'Error type',
                                        'Folder', 'Filename'])
            data = json.loads(get_distractors(data).to_json(orient="records"))

            if data:
                # for i in range(len(data)):
                #     data[i]['id'] = last_id + i +1
                questions = [Question(question_text=q['Sentence'],
                                    error_tag=q['Error type'], question_type='multiple_choice',
                                    question_level=0, ukey=ukey,
                                    batch_elem_id=i) for i, q in enumerate(data)]
                Question.objects.bulk_create(questions)

                questions = Question.objects.filter(ukey=ukey).order_by("batch_elem_id")
                answers = [
                    Answer(question_id=q, answer_text=data[q.batch_elem_id]["Right answer"])
                    for q in questions
                ]
                Answer.objects.bulk_create(answers)

                wrong_answers = []
            
                for record, question in zip(data, questions):
                    wrong_answers.append(
                        WrongAnswer(
                            question=question,
                            answer_text=record['Wrong answer']
                        )
                    )
                    for column in record:
                        if column.startswith('Distractor'):
                            if record[column]:
                                wrong_answers.append(
                                    WrongAnswer(
                                        question=question,
                                        answer_text=record[column],
                                        is_generated=True
                                    )
                                )

                WrongAnswer.objects.bulk_create(wrong_answers)
            else:
                return
        elif distractor_model == "disselector":
            records = [
                {
                    "Sentence": ex[0],
                    "Right answer": ex[1][0],
                    "Error type": ex[3]
                } for ex in exercises if ex[3] == "lex_item_choice" and
                    len(ex[1][0].split()) == 1
            ]
            if records:
                data = [
                    {
                        "id": idx,
                        "sentence": re.sub("<b>.*?</b>", "[MASK]", el['Sentence']),
                        "right_answer": el['Right answer']
                    } for idx, el in enumerate(records)
                ]
                distractors = get_distractors_from_disselector(data)

                questions = [
                    Question(
                        question_text=re.sub("<b>.*?</b>", "_"*8, q['Sentence']),
                        error_tag=q['Error type'], question_type='multiple_choice',
                        question_level=0, ukey=ukey, batch_elem_id=el['id']
                    ) for q, el, d in zip(records, data, distractors) if d
                ]
                distractors = [d for d in distractors if d]
                Question.objects.bulk_create(questions)

                questions = Question.objects.filter(ukey=ukey).order_by(
                    "batch_elem_id"
                )
                answers = [
                    Answer(
                        question_id=q,
                        answer_text=data[q.batch_elem_id]["correction"]
                    ) for q in questions
                ]
                Answer.objects.bulk_create(answers)

                wrong_answers = []

                for question, distractor_set in zip(questions, distractors):
                    for distractor in distractor_set:
                        wrong_answers.append(
                            WrongAnswer(
                                question=question,
                                answer_text=distractor,
                                is_generated=True,
                                distractor_model="disselector"
                            )
                        )

                WrongAnswer.objects.bulk_create(wrong_answers)
            else:
                return
    else:
        if strike:
            questions = [Question(question_text=ex[0].replace('<b>','<b><s>').replace('</b>', '</s></b>')
            ,error_tag=ex[3], question_type="short_answer", question_level=0, ukey=ukey, batch_elem_id=idx) for idx, ex in enumerate(exercises)]
        else:
            questions = [Question(question_text=ex[0], error_tag=ex[3],
            question_type="short_answer", question_level=0, ukey=ukey, batch_elem_id=idx) for idx, ex in enumerate(exercises)]
    
        Question.objects.bulk_create(questions)
        questions = Question.objects.filter(ukey=ukey).order_by("batch_elem_id")
        answers=[Answer(question_id=q, answer_text=ans) for ex, q in zip(exercises, questions) for ans in ex[1]]
        Answer.objects.bulk_create(answers)

    # generated_questions = Question.objects.filter(ukey=ukey)

    if new_qfolder:
        if not qfolder_name:
            qfolder_name = 'downloaded_'+testmaker.get_fname_time()
        qfolder = Folder(name=qfolder_name)
        qfolder.save()
        qfolder = Folder.objects.get(name=qfolder_name)
        qtf_table = Question.folder.through
        new_relations = [qtf_table(question=question,
        folder=qfolder) for question in questions]
        qtf_table.objects.bulk_create(new_relations)
