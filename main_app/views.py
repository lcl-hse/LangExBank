from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Sum
from django.urls import reverse


# Create your views here.

import html
import re
import random
import sys
import pandas as pd


from math import ceil
from transliterate import translit
from io import BytesIO
from collections import defaultdict, namedtuple


from .models import *
from .utils import *
from .management.commands.questions_from_folder import generate_questions
from testing_platform.settings import login_enc_key, encode, registration_open

from testmaker import realec_grammar_exercises_without_mc as testmaker
from conf_files.tags import tagset
from conf_files.tag_mapping import tag_map, map_tag


## Generating questions from REALEC essay with testmaker
## Displaying them to user
## Displaying questions generated from the essay
## And writing them to the database:
def show_generated_questions(request, coll, doc):
    if 'rights' in request.session:
        if request.session['rights'] == 'T' or request.session['rights'] == 'A':
            if request.POST:
                question_type = "short_answer"
                question_level = 0
                error_tag = "Suggestion"
                if "newQuiz" in request.POST:
                    strip_answers = False
                    if 'strip_answers' in request.POST:
                        strip_answers = True
                    newQuiz = Quizz(strip_answers=strip_answers)
                    newQuiz.save()
                    if request.POST["quizName"].strip():
                        newQuiz.name = request.POST["quizName"]
                    else:
                        newQuiz.name = "Quiz " + str(newQuiz.id)
                    if request.session["rights"] == "T":
                        curr_teacher = User.objects.get(login=request.session["user_id"])
                        newQuiz.teacher = curr_teacher
                    newQuiz.save()
                else:
                    newQuiz = None
                question_fields = [field for field in request.POST if re.fullmatch("question_[0-9]+", field)]
                answer_fields = [field for field in request.POST if re.fullmatch("answer_[0-9]+_[0-9]+", field)]
                question_field_mapping = dict()
                for question_field in question_fields:
                    question_number = int(question_field.split('_')[1])
                    new_question = Question(question_text = request.POST[question_field],
                    question_type = question_type, question_level = question_level,
                    error_tag = request.POST[question_field+"_"+"tag"])
                    new_question.save()
                    if newQuiz is not None:
                        new_question.quiz.add(newQuiz)
                    question_field_mapping[question_number] = new_question
                for answer_field in answer_fields:
                    question_number = int(answer_field.split('_')[1])
                    new_answer = Answer(question_id = question_field_mapping[question_number],
                    answer_text = request.POST[answer_field])
                    new_answer.save()
                return redirect('quiz_list')
            else:
                #временное решение - заменяем слеши в пути к файлу
                #на двойное подчёркивание, чтобы джанго и программист
                #не сходили с ума:
                essay_path = coll.replace(r"__",'/') + doc
                # почему-то падает (не выдаёт вопросов) на всех эссе, кроме /exam/exam2017/ABL_1_1
                # это всё потому, что хром переводит все буквы в названии эссе в uppercase (на мозилле всё ок)
                # (только если вбивать адрес руками)
                # print(essay_path)
                questions = testmaker.generate_exercises_from_essay(essay_path, context=True, exercise_types=['short_answer'],
                hier_choice=True, file_output=False, moodle_output=False)['short_answer']
                return render(request, 'generquestions.html', {'questions': enumerate(questions)})
    request.session["prev_page"] = reverse("show_generated_questions", args={"coll": coll,
                                                                             "doc": doc})
    return redirect('login')


def display_quiz(request, quiz_id):
    if request.POST and 'rights' in request.session:
        answer_fields = [field for field in request.POST if re.fullmatch("question_[0-9]+", field)]
        quizz = Quizz.objects.get(id=int(request.POST["quiz_id"]))
        student = User.objects.get(login=request.session["user_id"])
        # I think, temporarily
        # Not letting student submit the form for the second time:
        # print(request.session["user_id"])
        if Results.objects.filter(student=student, quizz = quizz).exists():
            return HttpResponse("You've already submitted this quiz")
        # for answer_field in answer_fields:
        #     user_answer = request.POST[answer_field].strip()
        #     if quizz.strip_answers:
        #         user_answer = user_answer.lower().strip(",:!.()-")
        #     question_id = int(answer_field.split('_')[1])
        #     question = Question.objects.get(id=question_id)
        #     right_answers = [i[0] for i in Answer.objects.filter(question_id=question).values_list('answer_text')]
        #     if quizz.strip_answers:
        #         right_answers = [i.lower() for i in right_answers]
        #     if user_answer in right_answers:
        #         mark = 1.0
        #     else:
        #         mark = 0.0
        #     ## если администратор или учитель уже пробовал тест, то обновляем уже существующий
        #     ## экзмепляр Results, а не создаём новый:
        #     try:
        #         result = Results.objects.get(student=student, quizz=quizz, question=question)
        #         result.answer = user_answer
        #         result.mark = mark
        #     except Results.DoesNotExist:
        #         result = Results(student=student, quizz=quizz, answer=user_answer,
        #         question=question, mark=mark)
        #     result.save()

        ## вариант с меньшим количеством обращений к базе данных:
        answer_fields = sorted(answer_fields, key=lambda x: int(x.split('_')[1]))
        answers = Answer.objects.filter(question_id__quiz=quizz).values_list('question_id', 'answer_text')
        right_answers = defaultdict(list)

        if quizz.strip_answers:
            for answer in answers:
                right_answers[answer[0]].append(answer[1].strip().strip(",:!.()-"))
        else:
            for answer in answers:
                right_answers[answer[0]].append(answer[1].strip())
        
        question_ids = [int(i.split('_')[1]) for i in answer_fields]
        questions = Question.objects.filter(id__in=question_ids).order_by('id')
        
        if quizz.strip_answers:
            results = [Results(student=student, quizz=quizz,
            question = question, answer = request.POST[answer_field],
            mark=float(request.POST[answer_field].strip().strip(",:!.()-") in right_answers[int(answer_field.split('_')[1])])) for answer_field,
            question in zip(answer_fields, questions)]
        else:
            results = [Results(student=student, quizz=quizz,
            question = question, answer = request.POST[answer_field],
            mark=float(request.POST[answer_field].strip() in right_answers[int(answer_field.split('_')[1])])) for answer_field,
            question in zip(answer_fields, questions)]
        
        Results.objects.bulk_create(results)
        ## конец варианта

        if request.session['rights'] in ('A', 'T'):
            return redirect('student_answers', quiz_id=quizz.id, student_id=request.session['user_id'])
        return redirect("index")
    elif 'rights' in request.session:
        quiz_questions = list(Question.objects.filter(quiz__id=quiz_id))#.values_list('id', 'question_text'))
        random.seed(User.objects.get(login=request.session["user_id"]))
        random.shuffle(quiz_questions)
        quiz_questions = quiz_questions[:50]
        for q in quiz_questions:
            if q.question_type == 'short_answer':
                q.question_text = split_by_span(q.question_text)
        return render(request, 'displayquiz.html', {'questions': enumerate(quiz_questions), 'quiz_id': quiz_id})
    else:
        request.session["prev_page"] = reverse("take_quiz", args={"quiz_id": quiz_id})
        return redirect('login')


def edit_quiz(request, quiz_id, page_num=1):

    ## чтобы открывать мог только админ или учитель, этот квиз создавший:
    if 'rights' in request.session:
        if 'q_p_page' in request.session:
            questions_per_page = request.session['q_p_page']
        else:
            questions_per_page = 20
            request.session['q_p_page'] = questions_per_page
            request.session.modified = True
        if request.session['rights'] == 'A':
            pass
        elif request.session['rights'] == 'T':
            if check_teacher(request.session["user_id"], quiz_id):
                pass
            else:
                return HttpResponse("You cannot edit quiz that you didn't create with Teacher rights")
        else:
            return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
        message = ''
        if request.POST:
            ## ЗДЕСЬ ПИШЕМ КОД ДЛЯ ИЗМЕНЕНИЯ ВОПРОСОВ В БАЗЕ:
            strip_answers = False
            if 'strip_answers' in request.POST:
                strip_answers = True
            quiz = Quizz.objects.get(id=quiz_id)
            quiz.strip_answers = strip_answers
            quiz.save()

            question_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("question_[0-9]+", field))
            answer_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("answer_[0-9]+_-?[0-9]+", field))
            wanswer_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("wanswer_[0-9]+_-?[0-9]+", field))

            delete_question_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("delete_[0-9]+", field))
            delete_answer_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("delete_[0-9]+_-?[0-9]+", field))
            delete_wanswer_fields = set(field[field.find('_')+8:] for field in request.POST if re.fullmatch("wrong_delete_[0-9]+_-?[0-9]+", field))

            question_fields.difference_update(delete_question_fields)
            answer_fields.difference_update(delete_answer_fields)
            wanswer_fields.difference(delete_wanswer_fields)

            for question_field in question_fields:
                question_id = int(question_field)
                question = Question.objects.get(id=question_id)
                question.question_text = request.POST["question_"+question_field]
                question.save()
                # print(question_field, question.question_text)
            for answer_field in answer_fields:
                question_id, answer_id = answer_field.split('_')
                question_id, answer_id = int(question_id), int(answer_id)
                ## пусть у ответов, создаваемых вручную через страницу /editQuiz/ будут отрицательные id:
                if answer_id < 0:
                    question = Question.objects.get(id=question_id)
                    answer = Answer(question_id=question, answer_text=request.POST["answer_"+answer_field])
                    answer.save()
                else:
                    answer = Answer.objects.get(id=answer_id)
                    answer.answer_text = request.POST["answer_"+answer_field]
                    answer.save()
                    # print(answer_field, answer.answer_text)
            for answer_field in wanswer_fields:
                question_id, answer_id = answer_field.split('_')
                question_id, answer_id = int(question_id), int(answer_id)
                ## пусть у ответов, создаваемых вручную через страницу /editQuiz/ будут отрицательные id:
                if answer_id < 0:
                    question = Question.objects.get(id=question_id)
                    answer = WrongAnswer(question=question, answer_text=request.POST["wanswer_"+answer_field])
                    answer.save()
                else:
                    answer = WrongAnswer.objects.get(id=answer_id)
                    answer.answer_text = request.POST["wanswer_"+answer_field]
                    answer.save()
                    # print(answer_field, answer.answer_text)

            for delete_question_field in delete_question_fields:
                ## delete many-to-many field that binds given question to given_quiz
                quiz = Quizz.objects.get(id=quiz_id)
                question = Question.objects.get(id=int(delete_question_field))
                question.quiz.remove(quiz)
            for delete_answer_field in delete_answer_fields:
                question_id, answer_id = delete_answer_field.split('_')
                question_id, answer_id = int(question_id), int(answer_id)
                if answer_id >= 0:
                    answer = Answer.objects.get(id=answer_id)
                    answer.delete()
            for delete_answer_field in delete_wanswer_fields:
                question_id, answer_id = delete_answer_field.split('_')
                question_id, answer_id = int(question_id), int(answer_id)
                if answer_id >= 0:
                    answer = WrongAnswer.objects.get(id=answer_id)
                    answer.delete()

            message = '<span style="color: white; background-color: green">Changes to quiz successfully saved</span>'
        elif request.GET:
            if 'question_id' in request.GET:
                question_to_return = Question.objects.get(id=request.GET['question_id'])
                return HttpResponse(question_to_return.question_text)
            elif 'answer_id' in request.GET:
                answer_to_return = Answer.objects.get(id=request.GET['answer_id'])
                return HttpResponse(answer_to_return.answer_text)
            elif 'wanswer_id' in request.GET:
                answer_to_return = WrongAnswer.objects.get(id=request.GET['wanswer_id'])
                return HttpResponse(answer_to_return.answer_text)
            elif 'max_q' in request.GET:
                qcount = request.GET['max_q']
                if isint(qcount):
                    if int(qcount) > 0:
                        questions_per_page = int(request.GET['max_q'])
                        request.session['q_p_page'] = questions_per_page
                        request.session.modified = True
        quiz = Quizz.objects.get(id=quiz_id)
        checked = ''
        if quiz.strip_answers:
            checked = "checked"
        if quiz.name is not None:
            quiz_identifier = quiz.name
        else:
            quiz_identifier = quiz.id
        quiz_questions = Question.objects.filter(quiz=quiz).order_by('id')
        count = quiz_questions.count()
        page_num -= 1
        if page_num * questions_per_page > count:
            page_num = ceil(count/questions_per_page)
        quiz_questions = quiz_questions[page_num*questions_per_page:(page_num+1)*questions_per_page]
        # for question in quiz_questions:
        #     question.append(tuple(Answer.objects.filter(question_id=question[0]).values_list('id', 'answer_text')))
        # print(quiz_questions)
        return render(request, 'editquiz.html', {'questions': enumerate(quiz_questions, start=questions_per_page*page_num), 'quiz_name': quiz_identifier, 'quiz_id': quiz.id,
        'message': message, 'checked': checked, 'page_nums': [i for i in range(1, ceil(count/questions_per_page)+1)], 'page': page_num+1, 'total_pages': ceil(count/questions_per_page)})
    else:
        request.session["prev_page"] = reverse("edit_quiz", args={"quiz_id": quiz_id, "page_num": page_num})
        # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
        return HttpResponseForbidden()


def quiz_list(request):
    if "rights" in request.session:
        if request.session["rights"] in ("T", "A"):
            request.session['q_p_page'] = 20
            request.session.modified = True
            if request.session["rights"] == "T":
                teacher = User.objects.get(login=request.session["user_id"])
                quizzes = Quizz.objects.filter(teacher=teacher).values_list('name', 'id')
            elif request.session["rights"] == "A":
                quizzes = Quizz.objects.all().values_list('name', 'id')
            return render(request, 'quizlist.html', {'quizlist':quizzes,
            'student': False})

        elif request.session["rights"] == "S":
            quizzes = Quizz.objects.all().values_list('name', 'id')
            return render(request, 'quizlist.html', {'quizlist':quizzes,
            'student': True})
        else:
            return HttpResponse("Authentication error")
    request.session["prev_page"] = reverse("quiz_list")
    return HttpResponseForbidden()


def login(request):
    if "logout" in request.GET:
        if "rights" in request.session:
            del request.session["rights"]
        if "password" in request.session:
            del request.session["password"]
        if "user_id" in request.session:
            del request.session["user_id"]
        if "prev_page" in request.session:
            del request.session["prev_page"]
    if "login" in request.POST:
        try:
            user = User.objects.get(login=request.POST['login'])
            if user.enc_password == request.POST["password"]:
                ##если логин и пароль есть в базе, добавляем
                ##в сессию логин и права:
                request.session["user_id"] = user.login
                request.session["rights"] = user.rights
                request.session.modified = True
                if 'prev_page' in request.session:
                    redirect_addr = request.session["prev_page"]
                    del request.session["prev_page"]
                    return redirect(redirect_addr)
                else:
                    return redirect("index")
            else:
                return render(request, 'login.html', {'message': '<span style="color: white; background-color: red"> Invalid password </span>'})
        except:
            return render(request, 'login.html', {'message': '<span style="color: white; background-color: red"> Invalid login </span>'})
    if 'prev_page' in request.session:
        message = '<span style="color: white; background-color: blue"> Please login as a teacher or admin to continue </span>'
    else:
        message = ''
    return render(request, 'login.html', {'message': message})


def index(request):
    if 'user_id' in request.session:
        return render(request, 'index.html')
    else:
        return redirect('login')


def quiz_grades(request, quiz_id, download=False, mask_names=True):
    ## to do -
    ## по умолчанию показывать только ответы студентов
    ## добавить возможность фильтрации ответов по группам студентов
    if 'rights' in request.session:
        if request.session["rights"] in ('T', 'A'):
            if request.session["rights"] == 'T':
                if not check_teacher(request.session["user_id"], quiz_id):
                    return HttpResponse("You cannot administer quiz that you didn't create with Teacher rights")
            quiz = Quizz.objects.get(id=quiz_id)
            quiz_results = Results.objects.filter(quizz = quiz)
            students = set(q.student for q in quiz_results)
            marks = {student: 0 for student in students}
            for student in students:
                marks[student] = quiz_results.filter(student=student).aggregate(Avg('mark'))['mark__avg']
            if mask_names:
                marks = [(student.login, mask_user(student), get_group(student), round(marks[student], 2)) for student in sorted(marks,
                key=lambda x: -marks[x])]
            else:
                marks = [(student.login, student.full_name, get_group(student), round(marks[student], 2)) for student in sorted(marks,
                key=lambda x: -marks[x])]
            if download:
                df = pd.DataFrame([i[1:] for i in marks],
                                 columns=('Full name', 'Group', 'Overall score'))
                stream = BytesIO()
                ExcelWriter = pd.ExcelWriter(stream, engine='openpyxl')
                df.to_excel(ExcelWriter)
                ExcelWriter.save()
                stream.seek(0)
                spreadsheet = stream.getvalue()
                response = HttpResponse(spreadsheet, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                fn = quiz.name
                response['Content-Disposition'] = f'attachment; filename="{fn}"".xlsx'
                return response
            else:
                download_url = f"/grades/{quiz_id}/download"
                return render(request, 'quiz_results.html', {'marks': marks,
                'quiz_name': quiz.name, 'quiz_id': quiz.id,
                'download_url': download_url})
        else:
            request.session["prev_page"] = reverse("quiz_grades", args={"quiz_id": quiz_id})
            return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    else:
        request.session["prev_page"] = reverse("quiz_grades", args={"quiz_id": quiz_id})
        # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
        return HttpResponseForbidden()

def download_grades(request, quiz_id):
    return quiz_grades(request, quiz_id, download=True)

def student_answers(request, quiz_id, student_id, download=False, mask_name=True):
    if request.session["rights"] in ("T", "A"):
        if request.session["rights"] == 'T':
            if not check_teacher(request.session["user_id"], quiz_id):
                return HttpResponse("You cannot administer quiz that you didn't create with Teacher rights")
        if request.POST:
            ## code for updating marks in the database:
            new_correct_ids = [(int(i.split('_')[1]), int(i.split('_')[2])) for i in request.POST if i.startswith("addRight")]
            new_answers = [Answer(question_id=Question.objects.get(id=item[0]),
            answer_text=Results.objects.get(id=item[1]).answer) for item in new_correct_ids]
            new_marks = [(int(key.split('_')[1]), float(value)) for key, value in request.POST.items() if key.startswith("mark") and is_float(value)]
            new_marks = [i for i in new_marks if i[1] >= 0 and i[1] <= 1]
            ## saving new right answers:
            Answer.objects.bulk_create(new_answers)
            ## updating results with the new correct answers:
            for new_answer in new_answers:
                Results.objects.filter(question=new_answer.question_id, answer=new_answer.answer_text).update(mark=1.0)
            for mark in new_marks:
                result = Results.objects.get(id=mark[0])
                result.mark = mark[1]
                result.save()
        student = User.objects.get(login = student_id)
        quiz = Quizz.objects.get(id = quiz_id)
        student_answers = Results.objects.filter(student = student,
        quizz = quiz).values_list('id', 'question__id', 'question__question_text', 'answer', 'mark', 'question__question_type')
        student_answers = [i[:5] + (";<br />".join(j[0] for j in Answer.objects.filter(question_id_id=i[1]).values_list("answer_text")),
        len(Results.objects.filter(question_id=i[1], mark=1.0))/len(Results.objects.filter(question_id=i[1])))+i[5:] for i in student_answers]
        if mask_name:
            student_name = mask_user(student)
        else:
            student_name = student.full_name
        quiz_name = quiz.name
        if download:
            student_answers = [i[1:] for i in student_answers]
            df = pd.DataFrame(student_answers, columns = ('Question ID', 'Question text', 'Answer',
            'Mark', 'Correct answers', 'Students correctly answered, %', 'Question type'))
            df['Correct answers'] = df['Correct answers'].str.replace(';<br />', ';\n')
            df['Students correctly answered, %'] = df['Students correctly answered, %'] * 100
            length = df.shape[0]
            df['Overall grade'] = pd.Series([f'=СУММ(E2:E{length+1})/{length}\n'] + ['' for i in range(length-1)])
            stream = BytesIO()
            ExcelWriter = pd.ExcelWriter(stream, engine='openpyxl')
            ##df.to_excel(quiz_name+' '+student_name+'.xlsx')
            df.to_excel(ExcelWriter)
            ExcelWriter.save()
            stream.seek(0)
            spreadsheet = stream.getvalue()
            response = HttpResponse(spreadsheet, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            fn = translit(quiz_name+' '+student_name, 'ru', reversed=True)
            # print(fn, type(fn))
            response['Content-Disposition'] = f'attachment; filename="{fn}"".xlsx'
            return response
        else:
            download_url = f"/grades/{quiz_id}/{student_id}/download"
            return render(request, 'student_results.html', {'student_answers': list(student_answers),
            'student_name': student_name, 'quiz_name': quiz_name,
            'download_url': download_url})  
    else:
        request.session["prev_page"] = reverse("student_answers", args={"quiz_id": quiz_id,
                                                                        "student_id": student_id})
        # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
        return HttpResponseForbidden()

def download_answers(request, quiz_id, student_id):
    return student_answers(request, quiz_id, student_id, download=True)

def filter_questions(sh_answer_questions, request, template, action_addr="/questions"):
    per_page = 40
    page = 0
    questions = [tuple(i) for i in sh_answer_questions.all().values_list('id', 'question_text')]
    err_tags = [(True, tag, map_tag(tag)) for tag in tagset]
    folders = [(True, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
    folders.insert(0, (True, 'None', 'None'))
    question_types = {'short_answer': True, 'multiple_choice': True}
    if request.GET:
        if 'filter' in request.GET:
            tags = [i[4:] for i in request.GET if i.startswith('tag_')]
            selected_folders = [i[7:] for i in request.GET if i.startswith('folder_')]
            selected_folders = [int(i) if i!='None' else None for i in selected_folders]
            selected_qtypes = [i[5:] for i in request.GET if i.startswith('type_')]
            questions = sh_answer_questions.filter(error_tag__in=tags).filter(folder__id__in=selected_folders).filter(question_type__in=selected_qtypes).values_list('id', 'question_text')
            for idx, err_tag in enumerate(err_tags):
                if err_tag[1] in tags:
                    err_tags[idx] = (True, err_tag[1], err_tag[2])
                else:
                    err_tags[idx] = (False, err_tag[1], err_tag[2])
            folders = [(i['id'] in selected_folders, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
            if None in selected_folders:
                questions |= sh_answer_questions.filter(error_tag__in=tags).filter(folder=None).filter(question_type__in=selected_qtypes).values_list('id', 'question_text')
                folders.insert(0, (True, 'None', 'None'))
            else:
                folders.insert(0, (False, 'None', 'None'))
            
            for qtype in question_types:
                if qtype not in selected_qtypes:
                    question_types[qtype] = False
            
        if 'page' in request.GET:
            try:
                new_page = int(request.GET['page'])
                if per_page*new_page < len(questions):
                    page = new_page
            except:
                pass
    start_index = page*per_page
    total_questions = len(questions)
    left_pages, right_pages = get_page_links(query=request.GET.dict(),
    page_id=page, total_questions=total_questions, per_page=per_page, step=3)
    questions = questions[start_index:start_index+per_page]
    question_types = list(question_types.items())
    return render(request, template, {'questions': questions, 'err_tags': err_tags, 'folders': folders,
    'types': question_types, 'left_pages': left_pages, 'right_pages': right_pages, 'page_id': page+1,
    'action_addr': action_addr})

def display_questions(request, err_type=None):
    if 'rights' in request.session:
        if request.session['rights'] == 'T' or request.session['rights'] == 'A':
            sh_answer_questions = Question.objects.filter(question_type__in=("short_answer", "multiple_choice"))
            if not request.POST:
                return filter_questions(sh_answer_questions, request, template='questions.html')
            else:
                if request.POST['item'] == 'quiz':
                    if request.POST["quizName"]:
                        quizName = request.POST["quizName"]
                    else:
                        quizName = 'Quiz ' + int(Quizz.objects.all().count())
                    questions_to_include = [int(i) for i in request.POST if request.POST[i] == "on" and isint(i)]
                    strip_answers = False
                    if 'strip_answers' in request.POST:
                        strip_answers = True
                    new_quiz = Quizz(name = quizName,
                    strip_answers = strip_answers)
                    if request.session['rights'] == 'T':
                        new_quiz.teacher = User.objects.get(login = request.session['user_id'])
                    new_quiz.save()
                    for question_id in questions_to_include:
                        included_question = sh_answer_questions.get(id = question_id)
                        included_question.quiz.add(new_quiz)
                        included_question.save()
                    return redirect('quiz_list')
                elif request.POST['item'] == 'folder':
                    if request.POST["folderName"]:
                        folderName = request.POST["folderName"]
                    else:
                        folderName = 'Folder ' + int(Folder.objects.all().count())
                    new_folder = Folder(name=folderName)
                    new_folder.save()
                    questions_to_include = [int(i) for i in request.POST if request.POST[i] == "on" and isint(i)]
                    ## adding questions to new folder:
                    questions = sh_answer_questions.filter(id__in=questions_to_include)
                    for q in questions:
                        q.folder.add(new_folder)
                        q.save()
                    return redirect('display_questions')
                else:
                    raise Exception('Incorrect request')
            
    request.session["prev_page"] = reverse("display_questions")
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()

def questions_from_folder(request):
    if 'rights' in request.session:
        if request.session['rights'] in ('A','T'):
            if request.POST:
                path = request.POST['path']
                tags = [field[4:] for field in request.POST if field.startswith('tag_')]
                if 'new_qfolder' in request.POST:
                    new_qfolder = True
                    if 'qfolder_name' in request.POST:
                        qfolder_name = request.POST['qfolder_name']
                ukey_prefix = request.session['user_id']
                multiple_choice = False
                if 'multiple_choice' in request.POST:
                    multiple_choice = True
                generate_questions(folder=path, tags=tags, strike=True, delete_downloaded=True,
                new_qfolder=new_qfolder, qfolder_name=qfolder_name, multiple_choice=multiple_choice)
                return redirect('display_questions')
            err_tags = [(False, tag, tag_map[tag]) if tag in tag_map else (False, tag, tag) for tag in tagset]
            return render(request, 'questions_from_folder.html',
            {'err_tags': err_tags})
    request.session["prev_page"] = reverse("questions_from_folder")
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()


def add_questions(request, quiz_id):
    if 'rights' in request.session:
        if request.session['rights'] == 'A' or request.session['rights'] == 'T':
            quiz = Quizz.objects.get(id=quiz_id)
            sh_answer_questions = Question.objects.filter(question_type__in=('short_answer', 'multiple_choice')).exclude(quiz__id=quiz_id)
            if request.POST:
                questions_to_include = [int(i) for i in request.POST if request.POST[i] == "on" and isint(i)]
                questions_to_include = Question.objects.filter(id__in=questions_to_include)
                for q in questions_to_include:
                    q.quiz.add(quiz)
                    q.save()
                return redirect('edit_quiz', quiz_id)
            return filter_questions(sh_answer_questions, request, template='add_questions.html',
                                    action_addr=f"/addQuestions/{quiz_id}")
            
    request.session["prev_page"] = reverse("add_questions", args={"quiz_id": quiz_id})
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()


def easy_register(request):
    if registration_open:
        if request.POST:
            if not 'login' in request.POST or is_field_zero(request.POST, 'login'):
                return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No login provided </span>'})
            if not 'password' in request.POST or is_field_zero(request.POST, 'password'):
                return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No password provided </span>'})
            if not 'full_name' in request.POST or is_field_zero(request.POST, 'full_name'):
                return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No full name provided </span>'})
            if not 'group' in request.POST or is_field_zero(request.POST, 'group'):
                return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No group provided </span>'})
            if User.objects.filter(login=request.POST['login']).exists():
                return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> User with this login already exists </span>'})
            else:
                new_student = User(login=request.POST['login'], full_name=request.POST['full_name'],
                enc_password=request.POST['password'], rights = 'S')
                new_student.save()
                new_student = Student(login=new_student, group=request.POST['group'])
                new_student.save()
                request.session["user_id"] = request.POST["login"]
                request.session["password"] = request.POST["password"]
                request.session["rights"] = "S"
                return redirect('quiz_list')
        return render(request, 'easy_register.html')
    else:
        return render(request, 'registration_closed.html')


def pdf_demo(request):
    return render(request, 'pdf_demo.html')

def edit_ielts_test(request, test_id=None):
    if "rights" in request.session:
        if request.session["rights"] in ("A", "T"):
            if request.POST:
                if test_id:
                    Test = IELTS_Test.objects.get(id=test_id)
                else:
                    Test = IELTS_Test(name=request.POST["testName"])
                    Test.save()
                ## Saving newly added questions to db:
                # print(request.POST)
                ## modifying existing sections:
                section_ids = [field for field in request.POST if field.startswith('section_') and not field.startswith('section_-')]
                for section_field in section_ids:
                    section_id = int(section_field.split('_')[1])
                    section = Section.objects.get(id=section_id)
                    section.text = request.POST[section_field]
                    section.name = request.POST[f"sec_name_{ section_id }"]
                    ## Working with attachment to the section:
                    section_type = request.POST[f"section-type_{ section_id }"]
                    if section_type != section.section_type:
                        if section_type == 'r':
                            section.section_type = section_type
                            if "pdf_upload_"+section_id in request.FILES:
                                section.attachment = request.FILES["pdf_upload_"+section_id]
                            else:
                                section.attachment = None
                        elif section_type == 'l':
                            section.section_type = section_type
                            if "audio_upload_"+section_id in request.FILES:
                                section.attachment = request.FILES["audio_upload_"+section_id]
                            else:
                                section.attachment = None
                        else:
                            raise Exception(f"Invalid attachment type - {section_type}")
                    ## If section type is unchanged,
                    ## changing file attachment only if a new file was attached:
                    else:
                        if section_type == 'r':
                            if f"pdf_upload_{ section_id }" in request.FILES:
                                if request.FILES[f"pdf_upload_{ section_id }"]:
                                    section.attachment = request.FILES[f"pdf_upload_{ section_id }"]
                        elif section_type == 'l':
                            if f"audio_upload_{ section_id }" in request.FILES:
                                if request.FILES[f"audio_upload_{ section_id }"]:
                                    section.attachment = request.FILES[f"audio_upload_{ section_id }"]
                    section.save()
                    ## Working with question fields:
                    ## Working with questions that previously existed:
                    question_fields = [field for field in request.POST if field.startswith(f"qtext_{section.id}") and not field.startswith(f"qtext_{section.id}_-")]
                    for question_field in question_fields:
                        q_id = int(question_field.split('_')[-1])
                        q = Question.objects.get(id=q_id)

                        if f"insensitive_{ section_id }_{ q_id }" in request.POST:
                            q.case_insensitive = True
                        q.save()

                        if f"sequence_{section_id}_{q_id}" in request.POST:
                            q.question_type = "ielts_multiple"
                        q.save()

                        ## Deleting previous answers:
                        Answer.objects.filter(question_id=q).delete()
                        WrongAnswer.objects.filter(question_id=q).delete()
                        
                        ## Writing new answers:
                        answers = request.POST[f'atext_{section_id}_{q_id}'].split(";")
                        for ans in answers:
                            a = Answer(question_id=q, answer_text=ans)
                            a.save()

                        multiple_key = f'wrong_{section_id}_{q_id}'

                        if multiple_key in request.POST:
                            wrong_answers = request.POST[multiple_key].split(";")
                            
                            wAnswers = [WrongAnswer(question=q, answer_text=wAnswer) for wAnswer in wrong_answers]
                            WrongAnswer.objects.bulk_create(wAnswers)
                    ## recheck results for modified questions:
                    question_ids = [int(i.split('_')[-1]) for i in question_fields]
                    recheck_answers(Results.objects.filter(question__id__in=question_ids))
                    ## Working with newly added questions:
                    question_fields = [field for field in request.POST if field.startswith(f"qtext_{section.id}_-")]
                    for question_field in question_fields:
                        q = Question(question_text=request.POST[question_field],
                                    question_type="ielts_question",
                                    question_level=0, section=section)
                        q_id = question_field.split('_')[-1]

                        if f"insensitive_{section_id}_{q_id}" in request.POST:
                            q.case_insensitive = True
                        q.save()

                        if f"sequence_{section_id}_{q_id}" in request.POST:
                            q.question_type = "ielts_multiple"
                        q.save()
                        
                        answers = request.POST[f"atext_{section_id}_{q_id}"].split(";")
                        for ans in answers:
                            a = Answer(question_id=q, answer_text=ans)
                            a.save()

                        multiple_key = f'wrong_{section_id}_{q_id}'

                        if multiple_key in request.POST:
                            wrong_answers = request.POST[multiple_key].split(";")
                            
                            wAnswers = [WrongAnswer(question=q, answer_text=wAnswer) for wAnswer in wrong_answers]
                            WrongAnswer.objects.bulk_create(wAnswers)
                ## deleting sections selected to delete:
                if "secs_to_delete" in request.POST:
                    delete_ids = [int(i) for i in request.POST["secs_to_delete"].split(';') if i]
                    secs_to_delete = Section.objects.filter(id__in=delete_ids)
                    secs_to_delete.delete()
                ## deleting questions selected to delete:
                if "questions_to_delete" in request.POST:
                    delete_ids = [int(i) for i in request.POST["questions_to_delete"].split(';') if i]
                    questions_to_delete = Question.objects.filter(id__in=delete_ids)
                    questions_to_delete.delete()
                ## adding new sections:
                new_section_ids = [field for field in request.POST if field.startswith('section_-')]
                for new_section in new_section_ids:
                    new_section_text = request.POST[new_section]
                    new_section_id = new_section.split('_')[1]
                    new_section_type = request.POST["section-type_"+new_section_id]
                    new_section_name = request.POST["sec_name_"+new_section_id]
                    if new_section_type == 'r':
                        if "pdf_upload_"+new_section_id in request.FILES:
                            new_section_attachment = request.FILES["pdf_upload_"+new_section_id]
                        else:
                            new_section_attachment = None
                    elif new_section_type == 'l':
                        if "audio_upload_"+new_section_id in request.FILES:
                            new_section_attachment = request.FILES["audio_upload_"+new_section_id]
                        else:
                            new_section_attachment = None
                    else:
                        raise Exception(f"Invalid attachment type - {new_section_type}")

                    section = Section(text=new_section_text, name=new_section_name,
                                    section_type=new_section_type, supplement=new_section_attachment)
                    section.save()
                    section.ielts_test.add(Test)
                    section.save()

                    question_fields = [field for field in request.POST if field.startswith('qtext_'+new_section_id)]
                    # print(question_fields)
                    for question_field in question_fields:
                        q = Question(question_text=request.POST[question_field],
                                    question_type="ielts_question",
                                    question_level=0, section=section)
                        q_id = question_field.split('_')[-1]

                        if "insensitive_"+new_section_id+"_"+q_id in request.POST:
                            q.case_insensitive = True
                        q.save()

                        if "sequence_"+new_section_id+"_"+q_id in request.POST:
                            q.question_type = "ielts_multiple"
                        q.save()
                        
                        answers = request.POST['atext_'+new_section_id+"_"+q_id].split(";")
                        for ans in answers:
                            a = Answer(question_id=q, answer_text=ans)
                            a.save()

                        multiple_key = 'wrong_'+str(new_section_id)+'_'+str(q_id)

                        if multiple_key in request.POST:
                            wrong_answers = request.POST[multiple_key].split(";")
                            
                            wAnswers = [WrongAnswer(question=q, answer_text=wAnswer) for wAnswer in wrong_answers]
                            WrongAnswer.objects.bulk_create(wAnswers)
                    
                Test.full_grade = full_grade(Test)
                Test.save()
                                    
                return redirect("ielts_test_list")
            else:
                if test_id:
                    test = IELTS_Test.objects.get(id=test_id)
                    test_sections = Section.objects.filter(ielts_test=test)
                    test_name = test.name
                    # for sec in test_sections:
                    #     sec.text = sec.text.replace('\n','\\\n')
                else:
                    test_sections = []
                    test_name = ''
                return render(request, "new_ielts_test.html", {'test_sections': test_sections,
                                                                         'test_name': test_name})
    request.session["prev_page"] = reverse("edit_ielts", args={'test_id': test_id})
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()

def ielts_test_list(request):
    if "rights" in request.session:
        if request.session["rights"] in ("T", "A"):
            tests = IELTS_Test.objects.all().values_list('name', 'id')
            return render(request, 'ielts_tests.html', {'quizlist': tests,
            'student': False})
        elif request.session["rights"] == "S":
            tests = IELTS_Test.objects.all().values_list('name', 'id')
            return render(request, 'ielts_tests.html', {'quizlist': tests,
            'student': True})
        else:
            return HttpResponse("Authentication error")
    request.session["prev_page"] = reverse('ielts_test_list')
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()

## здесь довольно громоздкая функция,
## надо бы оптимизировать,
## а то check_answers считается слишком долго - иногда страница с Results приходит раньще,
## чем они посчитаются
def take_ielts_test(request, test_id):
    if "rights" in request.session:
        if request.POST:
            if Results.objects.filter(student__login=request.session["user_id"],
             question__section__ielts_test__id = test_id).exists():
                return HttpResponse("You've already submitted this quiz")
            answer_fields = sorted([field for field in request.POST if field.startswith("question_")],
            key=lambda x: x.split("_")[1])
            question_ids = [int(i.split('_')[1]) for i in answer_fields]
            answers = [request.POST[answer_field] for answer_field in answer_fields]
            check_answers(answers, question_ids, request.session)
            if request.session["rights"] in ("A", "T"):
                return redirect("ielts_grades", test_id=test_id)
            elif request.session["rights"] == "S":
                return redirect("index")
        else:
            test = IELTS_Test.objects.get(id=test_id)
            sections = Section.objects.filter(ielts_test=test)

            ## Acessing the other side of foreign key the Django way!
            ## hint form https://stackoverflow.com/questions/9622047/django-accessing-foreignkey-model-objects:
            # task_set = [(section.name, section.text, section.supplement, section.section_type, 
            # section.question_set.all()) for section in sections]
            # print(task_set)
            return render(request, "displaytest.html", {"task_set": sections})
    request.session["prev_page"] = reverse("take_ielts", args={"test_id": test_id})
    return redirect('login')

def ielts_grades(request, test_id, mask_names=True):
    ## to do -
    ## по умолчанию показывать только ответы студентов
    ## добавить возможность фильтрации ответов по группам студентов
    if 'rights' in request.session:
        if request.session["rights"] in ('T', 'A'):
            test = IELTS_Test.objects.get(id=test_id)
            quiz_results = Results.objects.filter(question__section__ielts_test__id=test_id)
            students = set(q.student for q in quiz_results)
            marks = {student: 0 for student in students}
            for student in students:
                marks[student] = quiz_results.filter(student=student).aggregate(Sum('mark'))['mark__sum']#/test.full_grade
            if mask_names:
                marks = [(student.login, mask_user(student), get_group(student), round(marks[student], 2)) for student in sorted(marks,
                key=lambda x: -marks[x])]
            else:
                marks = [(student.login, student.full_name, get_group(student), round(marks[student], 2)) for student in sorted(marks,
                key=lambda x: -marks[x])]
            return render(request, 'ielts_results.html', {'marks': marks,
            'quiz_name': test.name, 'quiz_id': test.id})
        else:
            request.session["prev_page"] = reverse("ielts_grades", args={"test_id": test_id})
            return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    else:
        request.session["prev_page"] = reverse("ielts_grades", args={"test_id": test_id})
        # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
        return HttpResponseForbidden()


def student_test_results(request, test_id, student_id, download=False, mask_name=True):
    if 'rights' in request.session:
        if request.session["rights"] in ("T", "A"):
            # if request.session["rights"] == 'T':
            #     if not check_teacher(request.session["user_id"], quiz_id):
            #         return HttpResponse("You cannot administer quiz that you didn't create with Teacher rights")
            if request.POST:
                ## code for updating marks in the database:
                new_correct_ids = [(int(i.split('_')[1]), int(i.split('_')[2])) for i in request.POST if i.startswith("addRight")]
                new_answers = [Answer(question_id=Question.objects.get(id=item[0]),
                answer_text=Results.objects.get(id=item[1]).answer) for item in new_correct_ids]
                new_marks = [(int(key.split('_')[1]), float(value)) for key, value in request.POST.items() if key.startswith("mark") and is_float(value)]
                new_marks = [i for i in new_marks if i[1] >= 0 and i[1] <= 1]
                ## saving new right answers:
                Answer.objects.bulk_create(new_answers)
                ## updating results with the new correct answers:
                for new_answer in new_answers:
                    Results.objects.filter(question=new_answer.question_id, answer=new_answer.answer_text).update(mark=1.0)
                for mark in new_marks:
                    result = Results.objects.get(id=mark[0])
                    result.mark = mark[1]
                    result.save()
            student = User.objects.get(login = student_id)
            test = IELTS_Test.objects.get(id = test_id)
            student_answers = Results.objects.filter(student = student,
            question__section__ielts_test = test).values_list('id', 'question__id', 'question__question_text', 'answer', 'mark')
            student_answers = [i + (";<br />".join(j[0] for j in Answer.objects.filter(question_id_id=i[1]).values_list("answer_text")),
            len(Results.objects.filter(question_id=i[1], mark=1.0))/len(Results.objects.filter(question_id=i[1]))) for i in student_answers]
            if mask_name:
                student_name = mask_user(student)
            else:
                student_name = student.full_name
            quiz_name = test.name
            if download:
                student_answers = [i[1:] for i in student_answers]
                df = pd.DataFrame(student_answers, columns = ('Question ID', 'Question text', 'Answer',
                'Mark', 'Correct answers', 'Students correctly answered, %'))
                df['Correct answers'] = df['Correct answers'].str.replace(';<br />', ';\n')
                df['Students correctly answered, %'] = df['Students correctly answered, %'] * 100
                length = df.shape[0]
                df['Overall grade'] = pd.Series([f'=СУММ(E2:E{length+1})/{length}\n'] + ['' for i in range(length-1)])
                stream = BytesIO()
                ExcelWriter = pd.ExcelWriter(stream, engine='openpyxl')
                ##df.to_excel(quiz_name+' '+student_name+'.xlsx')
                df.to_excel(ExcelWriter)
                ExcelWriter.save()
                stream.seek(0)
                spreadsheet = stream.getvalue()
                response = HttpResponse(spreadsheet, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                fn = translit(quiz_name+' '+student_name, 'ru', reversed=True)
                # print(fn, type(fn))
                response['Content-Disposition'] = f'attachment; filename="{fn}"".xlsx'
                return response
            else:
                download_url = f"/IELTSgrades/{test_id}/{student_id}/download"
                return render(request, 'student_results.html', {'student_answers': list(student_answers),
                'student_name': student_name, 'quiz_name': quiz_name,
                'download_url': download_url})       
    request.session["prev_page"] = reverse("student_test_results", args={"test_id": test_id,
    "student_id": student_id})
    # return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    return HttpResponseForbidden()

def download_ielts_results(request, test_id, student_id):
    return student_test_results(request, test_id, student_id, download=True)

def delete_test(request):
    if "rights" in request.session:
        if request.session['rights'] in ('A', 'T'):
            if 'test_id' in request.POST:
                test_id = request.POST["test_id"]
                test = IELTS_Test.objects.get(id=test_id)
                test.delete()
                return HttpResponse("OK")
    return HttpResponseForbidden()

def delete_quiz(request):
    if "rights" in request.session:
        if request.session['rights'] in ('A', 'T'):
            if 'quiz_id' in request.POST:
                quiz_id = request.POST["quiz_id"]
                quiz = Quizz.objects.get(id=quiz_id)
                quiz.delete()
                return HttpResponse("OK")
    return HttpResponseForbidden()

def distractor_report(request, quiz_id):
    if 'rights' in request.session:
        if request.session['rights'] in ('A', 'T'):
            quiz = Quizz.objects.get(id=quiz_id)
            results = Results.objects.filter(quizz=quiz)
            output = dict()
            output['quiz_info'] = {'Quiz name': quiz.name,
                           'Quiz id': quiz_id}
            output['quiz_data'] = []
            for result in results:
                item = {
                    'student': result.student.login,
                    'role': result.student.rights,
                    'question_id': result.question.id,
                    'question': result.question.question_text,
                    'submitted_answer': result.answer,
                    'right answers': result.question.get_right_answers_text(),
                    'mark': result.mark,
                    'is generated distractor': result.answer in result.question.get_generated_distractors()
                }
                output['quiz_data'].append(item)
            return JsonResponse(output)
    return HttpResponseForbidden()
