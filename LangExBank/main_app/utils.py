import base64
import re
import ast

from math import ceil
from collections import namedtuple

from main_app.models import *
from testing_platform.settings import login_enc_key, encode

PageLink = namedtuple('PageLink', ['text', 'link'])

def is_field_zero(d, field_name):
    try:
        if d[field_name]:
            return False
        else:
            return True
    except KeyError:
        return True

def query_to_str(query):
    s = '?'
    s += '&'.join([key+'='+str(value) for key, value in query.items()])
    return s


## Для нумерной страницы
## получаем HTML-элементы с ссылками
## на другие нумерные страницы
def get_page_links(query, page_id, total_questions, per_page, step):
    n_pages = ceil(total_questions/per_page)

    left_pages, right_pages = [], []

    query['page'] = 0
    left_pages.append(PageLink('<< To First', query_to_str(query)))

    for i in range(max(0,page_id-step+1), page_id):
        query['page'] = str(i)
        left_pages.append(PageLink(str(i+1), query_to_str(query)))
    
    for i in range(page_id+1, min(page_id+step, n_pages)):
        query['page'] = str(i)
        right_pages.append(PageLink(str(i+1), query_to_str(query)))
    
    query['page'] = n_pages-1
    right_pages.append(PageLink('>> To Last', query_to_str(query)))

    return left_pages, right_pages


def check_teacher(user_id, quiz_id):
    try:
        if user_id == Quizz.objects.get(id = quiz_id).teacher.login:
            return True
        else:
            return False
    except AttributeError:
        return False

## Возвращаем группу студента,
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

def split_by_span(text):
    '''Returns left and right contexts of error span
    from a sentence with error
    
    Args:
     - text - string with an error span inside <b> or <strong> HTML tag, e.g.
              "It was a <b><strike>loving</strike></b> day."
    Returns:
     - left - left context of an error, e.g.
              "It was a "
     - right - right context of an error, e.g.
               " day."
    '''
    endmark = '</b>'
    endmark_id = text.rfind(endmark)
    if endmark_id == -1:
        endmark = '</strong>'
        endmark_id = text.rfind(endmark)
    split_ind = endmark_id + len(endmark)
    return text[:split_ind], text[split_ind:]

## Taken from https://stackoverflow.com/a/38223403

def encrypt(key, clear):
    '''Encrypts a string'''
    if encode:
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc).encode()).decode()
    return clear

def decrypt(key, enc):
    '''Decrypts a string'''
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def mask_user(user):
    '''Create encrypted string
       representation of a User object'''
    if encode:
        if user.rights == 'S':
            masked_name = f'student_{encrypt(login_enc_key, user.login)}'
        elif user.rights == 'T':
            masked_name = f'teacher_{encrypt(login_enc_key, user.login)}'
        elif user.rights == 'A':
            masked_name = f'admin_{encrypt(login_enc_key, user.login)}'
        else:
            masked_name = f'user_{encrypt(login_enc_key, user.login)}'
    else:
        if user.rights == 'S':
            masked_name = f'Student {user.full_name}'
        elif user.rights == 'T':
            masked_name = f'Teacher {user.full_name}'
        elif user.rights == 'A':
            masked_name = f'Admin {user.full_name}'
        else:
            masked_name = f'User {user.full_name}'
    return masked_name

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
    question_ids = sorted(question_ids)

    questions = Question.objects.filter(id__in=question_ids).order_by('id')
    right_answers = [(ans.answer_text, ans.question_id.id) for ans in Answer.objects.filter(question_id__id__in = question_ids).order_by('id')]

    right_answers = {ans[1]: [i[0] for i in right_answers if i[1] == ans[1]] for ans in right_answers}

    check_sheet = []

    for answer, qid, question in zip(answers, question_ids, questions):
        #print(answer, question)
        if question.multi_field:
            answered = True
            ## check >1 fields and get score only for 100% correspondence:
            ## The order of answers is preserved via ID field
            for ans, right_values in zip(answer, right_answers[qid]):
                ans = ans.strip()
                if question.case_insensitive:
                    ans = ans.lower()
                    right_values = right_values.lower()
                if ans not in (i.strip() for i in right_values.split(';')):
                    answered = False
                    break
            if answered:
                check_sheet.append(1.0)
            else:
                check_sheet.append(0.0)

        else:
            if question.question_type == "ielts_multiple":
                check_sheet.append(check_multiple(answer, right_answers[qid]))
            else:
                if question.case_insensitive:
                    if answer.strip().lower() in [i.strip().lower() for i in right_answers[qid]]:
                        check_sheet.append(1.0)
                    else:
                        check_sheet.append(0.0)
                else:
                    if answer.strip() in [i.strip() for i in right_answers[qid]]:
                        check_sheet.append(1.0)
                    else:
                        check_sheet.append(0.0)
    
    user = User.objects.get(login = session["user_id"])

    Results.objects.bulk_create([Results(student = User.objects.get(login=session["user_id"]),
                                         question = q,
                                         answer = str(answer),
                                         mark = mark) for answer, q, mark in zip(answers, questions, check_sheet)])

def recheck_answers(results):
    for result in results:
        right_answers = [i.answer_text for i in result.question.answer_set.all().order_by('id')]
        if result.question.question_type == "ielts_multiple":
            result.mark = check_multiple(result.answer, right_answers)
        elif result.question.question_type == "ielts_question":
            if result.question.multi_field:
                answered = True
                ## check >1 fields and get score only for 100% correspondence:
                ## The order of answers is preserved via ID field
                for ans, right_values in zip(ast.literal_eval(result.answer), right_answers):
                    ans = ans.strip()
                    if result.question.case_insensitive:
                        ans = ans.lower()
                        right_values = right_values.lower()
                    if ans not in (i.strip() for i in right_values.split(';')):
                        answered = False
                        break
                if answered:
                    result.mark = 1.0
                else:
                    result.mark = 0.0
            else:
                for right_answer in right_answers:
                    if result.question.case_insensitive:
                        if result.answer.lower().strip() == right_answer.lower().strip():
                            result.mark = 1.0
                    else:
                        if result.answer.strip() == right_answer.strip():
                            result.mark = 1.0
        result.save()

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


## checks whether this user has access to provided page:
def has_access(user, page):
    ## пока костыльно,
    ## потом можно будет
    ## переписать по-нормальному
    if user.rights in ('A','T'):
        return True
    elif user.rights == 'S':
        page_lc = page.lower()
        if 'edit' in page_lc or 'review' in page_lc\
        or 'grades' in page_lc or 'delete' in page_lc\
        or 'folder' in page_lc or 'questions' in page_lc:
            return False
        else:
            return True
    return False

## Decorators

## Decorator for deleting session data after leaving restricted-acces page:
def del_prev_page(view):
    def wrapper_del_prev_page(request, *args, **kwargs):
        if "prev_page" in request.session:
            del request.session["prev_page"]
        if "asked_restricted" in request.session:
            del request.session["asked_restricted"]
        request.session.modified = True
        return view(request, *args, **kwargs)
    return wrapper_del_prev_page