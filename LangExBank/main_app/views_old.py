from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Sum

# Create your views here.

import html
import re
import random
import sys
import pandas as pd


from math import floor, ceil
from transliterate import translit
from io import BytesIO
from collections import defaultdict


from .models import *
from .management.commands.questions_from_folder import generate_questions

from testmaker import realec_grammar_exercises_without_mc as testmaker
from conf_files.tags import tagset
from conf_files.tag_mapping import tag_map


def check_teacher(user_id, quiz_id):
    try:
        if user_id == Quizz.objects.get(id = quiz_id).teacher.login:
            return True
        else:
            return False
    except AttributeError:
        return False

def get_group(user):
    try:
        return user.student.group
    except User.student.RelatedObjectDoesNotExist:
        if user.rights == 'T':
            return 'Teacher'
        elif user.rights == 'S':
            return 'Admin'

def is_float(string):
    return string.replace(".", '', 1).isdigit()

def isint(string):
    try:
        int(string)
        return True
    except:
        return False

def split_by_span(questions, endmark='</b>'):
    questions = list(questions)
    for idx, question in enumerate(questions):
        db_id = question[0]
        text = question[1]
        split_ind = text.rfind(endmark) + len(endmark)
        questions[idx] = (db_id, (text[:split_ind], text[split_ind:]))
    return questions

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
                print(essay_path)
                questions = testmaker.generate_exercises_from_essay(essay_path, context=True, exercise_types=['short_answer'],
                hier_choice=True, file_output=False, moodle_output=False)['short_answer']
                return render(request, 'generquestions.html', {'questions': enumerate(questions)})
    request.session["prev_page"] = f'/generateQuestions/{coll}/{doc}'
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
        quiz_questions = split_by_span(Question.objects.filter(quiz__id=quiz_id).values_list('id', 'question_text'))
        random.seed(User.objects.get(login=request.session["user_id"]))
        random.shuffle(quiz_questions)
        quiz_questions = quiz_questions[:50]
        return render(request, 'displayquiz.html', {'questions': enumerate(quiz_questions), 'quiz_id': quiz_id})
    else:
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
            delete_question_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("delete_[0-9]+", field))
            delete_answer_fields = set(field[field.find('_')+1:] for field in request.POST if re.fullmatch("delete_[0-9]+_-?[0-9]+", field))
            question_fields.difference_update(delete_question_fields)
            answer_fields.difference_update(delete_answer_fields)
            question_field_mapping = dict()
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
            message = '<span style="color: white; background-color: green">Changes to quiz successfully saved</span>'
        elif request.GET:
            if 'question_id' in request.GET:
                question_to_return = Question.objects.get(id=request.GET['question_id'])
                return HttpResponse(question_to_return.question_text)
            elif 'answer_id' in request.GET:
                answer_to_return = Answer.objects.get(id=request.GET['answer_id'])
                return HttpResponse(answer_to_return.answer_text)
            elif 'max_q' in request.GET:
                qcount = request.GET['max_q']
                if isint(qcount):
                    if int(qcount) > 0:
                        questions_per_page = int(request.GET['max_q'])
                        # page_num = floor((request.session['q_p_page'] * page_num)/questions_per_page)
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
        quiz_questions = Question.objects.filter(quiz=quiz)
        count = quiz_questions.count()
        page_num -= 1
        if page_num * questions_per_page > count:
            page_num = ceil(count/questions_per_page)
        quiz_questions = [list(i) for i in quiz_questions.values_list('id', 'question_text')][page_num*questions_per_page:(page_num+1)*questions_per_page]
        for question in quiz_questions:
            question.append(tuple(Answer.objects.filter(question_id=question[0]).values_list('id', 'answer_text')))
        # print(quiz_questions)
        return render(request, 'editquiz.html', {'questions': enumerate(quiz_questions, start=questions_per_page*page_num), 'quiz_name': quiz_identifier, 'quiz_id': quiz.id,
        'message': message, 'checked': checked, 'page_nums': [i for i in range(1, ceil(count/questions_per_page)+1)], 'page': page_num+1, 'total_pages': ceil(count/questions_per_page)})
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


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
            'student': False, 'results': False})

        elif request.session["rights"] == "S":
            quizzes = Quizz.objects.all().values_list('name', 'id')
            return render(request, 'quizlist.html', {'quizlist':quizzes,
            'student': True, 'results': False})
        else:
            return HttpResponse("Authentication error")
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


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
            if user.password == request.POST["password"]:
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



def show_results(request):
    if 'rights' in request.session:
        if request.session["rights"] == 'S':
            student_results = Results.objects.filter(student=User.objects.get(login=request.session['user_id']))
            ## здесь пишем код, который показывает на странице результаты всех квизов,
            ## которые сдавал студент
            raise NotImplementedError
        else:
            if request.session['rights'] in ('T', 'A'):
                if request.session["rights"] == 'T':
                    quizzes = Quizz.objects.filter(teacher=User.objects.get(login=request.session['user_id'])).values_list('name', 'id')
                elif request.session["rights"] == 'A':
                    quizzes = Quizz.objects.all().values_list('name', 'id')
                return render(request, 'quizlist.html', {'quizlist': quizzes,
                'student': False, 'results': True})
            else:
                return HttpResponse("Authentication error")
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def quiz_grades(request, quiz_id):
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
            marks = [(student.login, student.full_name, get_group(student), round(marks[student], 2)) for student in sorted(marks,
            key=lambda x: -marks[x])]
            return render(request, 'quiz_results.html', {'marks': marks,
            'quiz_name': quiz.name, 'quiz_id': quiz.id})
        else:
            return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def student_answers(request, quiz_id, student_id, download=False):
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
        quizz = quiz).values_list('id', 'question__id', 'question__question_text', 'answer', 'mark')
        student_answers = [i + (";<br />".join(j[0] for j in Answer.objects.filter(question_id_id=i[1]).values_list("answer_text")),
        len(Results.objects.filter(question_id=i[1], mark=1.0))/len(Results.objects.filter(question_id=i[1]))) for i in student_answers]
        student_name = student.full_name
        quiz_name = quiz.name
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
            print(fn, type(fn))
            response['Content-Disposition'] = f'attachment; filename="{fn}"".xlsx'
            return response
        else:
            download_url = f"/grades/{quiz_id}/{student_id}/download"
            return render(request, 'student_results.html', {'student_answers': list(student_answers),
            'student_name': student_name, 'quiz_name': quiz_name,
            'download_url': download_url})  
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def download_answers(request, quiz_id, student_id):
    return student_answers(request, quiz_id, student_id, download=True)

def display_questions(request, err_type=None):
    per_page = 40
    page = 0
    if 'rights' in request.session:
        if request.session['rights'] == 'T' or request.session['rights'] == 'A':
            sh_answer_questions = Question.objects.filter(question_type="short_answer")
            if request.GET:
                if 'filter' in request.GET:
                    tags = [i[4:] for i in request.GET if i.startswith('tag_')]
                    selected_folders = [i[7:] for i in request.GET if i.startswith('folder_')]
                    selected_folders = [int(i) if i!='None' else None for i in selected_folders]
                    questions = sh_answer_questions.filter(error_tag__in=tags).filter(folder__id__in=selected_folders).values_list('id', 'question_text')
                    all_tags = sh_answer_questions.order_by('error_tag').values('error_tag').distinct()
                    err_tags = [(i['error_tag'] in tags, i['error_tag'], i['error_tag']) for i in all_tags]
                    folders = [(i['id'] in selected_folders, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
                    if None in selected_folders:
                        questions |= sh_answer_questions.filter(error_tag__in=tags).filter(folder=None).values_list('id', 'question_text')
                        folders.insert(0, (True, 'None', 'None'))
                    else:
                        folders.insert(0, (False, 'None', 'None'))
            if not request.GET or (request.GET and 'filter' not in request.GET):
                questions = [tuple(i) for i in sh_answer_questions.all().values_list('id', 'question_text')]
                err_tags = [(True, i['error_tag'], i['error_tag']) for i in sh_answer_questions.order_by('error_tag').values('error_tag').distinct()]
                folders = [(True, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
                folders.insert(0, (True, 'None', 'None'))
            if request.GET:
                if 'page' in request.GET:
                    try:
                        new_page = int(request.GET['page'])
                        print(new_page)
                        if per_page*new_page < len(questions):
                            page = new_page
                    except:
                        pass
            if request.POST:
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
            # for question in all_questions:
            #     question.append(tuple(Answer.objects.filter(question_id=question[0]).values_list('id', 'answer_text')))
            print(page)
            start_index = page*per_page
            questions = questions[start_index:start_index+per_page]
            print(len(questions))
            return render(request, 'questions_bootstrap.html', {'questions': questions, 'err_tags': err_tags, 'folders': folders})
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


def questions_from_folder(request):
    if 'rights' in request.session:
        if request.session['rights'] in ('A','T'):
            if request.POST:
                path = request.POST['path']
                tags = [field[4:] for field in request.POST if field.startswith('tag_')]
                generate_questions(folder=path, tags=tags, strike=True, delete_downloaded=True)
                return redirect('display_questions')
            err_tags = [(False, tag, tag_map[tag]) if tag in tag_map else (False, tag, tag) for tag in tagset]
            return render(request, 'questions_from_folder.html',
            {'err_tags': err_tags})
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


def add_questions(request, quiz_id):
    if 'rights' in request.session:
        if request.session['rights'] == 'A' or request.session['rights'] == 'T':
            quiz = Quizz.objects.get(id=quiz_id)
            if request.POST:
                if 'filter' in request.POST:
                    tags = [i[4:] for i in request.POST if i.startswith('tag_')]
                    selected_folders = [i[7:] for i in request.POST if i.startswith('folder_')]
                    selected_folders = [int(i) if i!='None' else None for i in selected_folders]
                    questions = Question.objects.exclude(quiz__id=quiz_id).filter(error_tag__in=tags).filter(folder__id__in=selected_folders).values_list('id', 'question_text')
                    all_tags = Question.objects.order_by('error_tag').values('error_tag').distinct()
                    err_tags = [(i['error_tag'] in tags, i['error_tag'], i['error_tag']) for i in all_tags]
                    folders = [(i['id'] in selected_folders, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
                    if None in selected_folders:
                        questions |= Question.objects.exclude(quiz__id=quiz_id).filter(error_tag__in=tags).filter(folder=None).values_list('id', 'question_text')
                        folders.insert(0, (True, 'None', 'None'))
                    else:
                        folders.insert(0, (False, 'None', 'None'))
                else:
                    questions_to_include = [int(i) for i in request.POST if request.POST[i] == "on" and isint(i)]
                    questions_to_include = Question.objects.filter(id__in=questions_to_include)
                    for q in questions_to_include:
                        q.quiz.add(quiz)
                        q.save()
                    return redirect('edit_quiz', quiz_id)
            else:
                questions = [tuple(i) for i in Question.objects.exclude(quiz__id=quiz_id).values_list('id', 'question_text')]
                err_tags = [(True, i['error_tag'], i['error_tag']) for i in Question.objects.order_by('error_tag').values('error_tag').distinct()]
                folders = [(True, i['id'], i['name']) for i in Folder.objects.all().values('id','name')]
                folders.insert(0, (True, 'None', 'None'))
            
            return render(request, 'add_questions.html', {'quiz_name': quiz.name, 'questions': questions, 'err_tags': err_tags, 'folders': folders})
            
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


def easy_register(request):
    if request.POST:
        if not 'login' in request.POST:
            return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No login provided </span>'})
        if not 'password' in request.POST:
            return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No password provided </span>'})
        if not 'full_name' in request.POST:
            return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No full name provided </span>'})
        if not 'group' in request.POST:
            return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> No group provided </span>'})
        if User.objects.filter(login=request.POST['login']).exists():
            return render(request, 'easy_register.html', {'message': '<span style="color: white; background-color: red"> User with this login already exists </span>'})
        else:
            new_student = User(login=request.POST['login'], full_name=request.POST['full_name'],
            password=request.POST['password'], rights = 'S')
            new_student.save()
            new_student = Student(login=new_student, group=request.POST['group'])
            new_student.save()
            request.session["user_id"] = request.POST["login"]
            request.session["password"] = request.POST["password"]
            request.session["rights"] = "S"
            return redirect('quiz_list')
    return render(request, 'easy_register.html')


def pdf_demo(request):
    return render(request, 'pdf_demo.html')

# def question_containers(request):
#     return render(request, "question_containers.html")

# def get_host(request):
#     return HttpResponse(request.META['http_host'])

# def test_uploads(request):
#     if request.POST:
#         print({key: val for key, val in request.POST.items() if not key.startswith("section_")})
#         return HttpResponse("Testing uploading files")
#     else:
#         return render(request, "playaudio.html")

# def test_media_folder(request):
#     print(settings.MEDIA_ROOT, settings.BASE_DIR)
#     return HttpResponse(settings.MEDIA_ROOT)

def get_section_contents(section_id):
    raise NotImplementedError

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
                        if "sequence_"+new_section_id+"_"+q_id in request.POST:
                            q.question_type = "ielts_multiple"
                        q.save()
                        
                        answers = request.POST['atext_'+new_section_id+"_"+q_id].split(";")
                        for ans in answers:
                            a = Answer(question_id=q, answer_text=ans)
                            a.save()
                    
                Test.full_grade = full_grade(Test)
                Test.save()
                
                ## Editing existing sections in db:
                    
                return redirect("ielts_test_list")
            else:
                if test_id:
                    test = IELTS_Test.objects.get(id=test_id)
                    sections = Section.objects.filter(ielts_test=test)
                    test_sections = [(sec.id, get_section_contents(sec.id)) for sec in sections]
                else:
                    return render(request, "edit_ielts_test.html", {'test_sections': []})
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

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
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def check_multiple(answer, right_answers):
    pattern = "[a-zA-Z]"
    letters = set([i.lower() for i in re.findall(pattern, answer)])

    max_mark = 0.0

    for right_answer in right_answers:
        right_letters = set([i.lower() for i in re.findall(pattern, right_answer)]) 
        if letters==right_letters:
            return float(len(letters))
        len_intersec = len(right_letters&letters)
        if len_intersec > max_mark:
            max_mark = len_intersec
    
    return max_mark


def check_answers(answers, question_ids, session):
    questions = Question.objects.filter(id__in=question_ids).order_by('id')
    right_answers = [(ans.answer_text, ans.question_id.id) for ans in Answer.objects.filter(question_id__id__in = question_ids)]

    right_answers = {ans[1]: [i[0] for i in right_answers if i[1] == ans[1]] for ans in right_answers}

    check_sheet = []

    for answer, qid, question in zip(answers, question_ids, questions):
        if question.question_type == "ielts_multiple":
            check_sheet.append(check_multiple(answer, right_answers[qid]))
        else:
            if answer.strip() in [i.strip() for i in right_answers[qid]]:
                check_sheet.append(1.0)
            else:
                check_sheet.append(0.0)
    
    user = User.objects.get(login = session["user_id"])

    Results.objects.bulk_create([Results(student = User.objects.get(login=session["user_id"]),
                                         question = q,
                                         answer = answer,
                                         mark = mark) for answer, q, mark in zip(answers, questions, check_sheet)])

def recheck_answers(results):
    for result in results:
        right_answers = [i.answer_text for i in Answer.objects.filter(question_id = result.question)]
        if result.question.question_type == "ielts_multiple":
            result.mark = check_multiple(result.answer, right_answers)
        elif result.question.question_type == "ielts_question":
            for right_answer in right_answers:
                if result.answer.strip() == right_answer.strip():
                    result.mark = 1.0
        result.save()

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
        
    return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def full_grade(test):
    questions = Question.objects.filter(section__ielts_test = test)

    q1 = questions.filter(question_type="ielts_question")
    q2 = questions.filter(question_type="ielts_multiple")

    full_grade = len(q1)

    pattern = '[a-zA-Z]'

    for q in q2:
        ans = Answer.objects.filter(question_id=q)[0]
        full_grade += len(re.findall(pattern, ans.answer_text))
    
    return full_grade

def ielts_grades(request, test_id):
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
            marks = [(student.login, student.full_name, get_group(student), round(marks[student], 2)) for student in sorted(marks,
            key=lambda x: -marks[x])]
            return render(request, 'ielts_results.html', {'marks': marks,
            'quiz_name': test.name, 'quiz_id': test.id})
        else:
            return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')


def student_test_results(request, test_id, student_id, download=False):
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
        test = IELTS_Test.objects.get(id = test_id)
        student_answers = Results.objects.filter(student = student,
        question__section__ielts_test = test).values_list('id', 'question__id', 'question__question_text', 'answer', 'mark')
        student_answers = [i + (";<br />".join(j[0] for j in Answer.objects.filter(question_id_id=i[1]).values_list("answer_text")),
        len(Results.objects.filter(question_id=i[1], mark=1.0))/len(Results.objects.filter(question_id=i[1]))) for i in student_answers]
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
            print(fn, type(fn))
            response['Content-Disposition'] = f'attachment; filename="{fn}"".xlsx'
            return response
        else:
            download_url = f"/IELTSgrades/{test_id}/{student_id}/download"
            return render(request, 'student_results.html', {'student_answers': list(student_answers),
            'student_name': student_name, 'quiz_name': quiz_name,
            'download_url': download_url})  
    else:
        return HttpResponse('You are not logged in as a teacher or admin. <a href="/login/">Login here</a>')

def download_ielts_results(request, test_id, student_id):
    return student_test_results(request, test_id, student_id, download=True)


def test_ajax(request):
    if request.POST:
        print("POST request OK")
        print(request.session["user_id"])
        print(request.session["rights"])
        return HttpResponse("POST Request OK")
    else:
        raise Exception

def display_users(request):
    ## Only for Admin users:
    raise NotImplementedError

    
def display_student_page():
    raise NotImplementedError


def display_teacher_page():
    raise NotImplementedError
