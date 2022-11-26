from django.db import models
from django.conf import settings
from encrypted_fields import fields

from random import shuffle

# requires package django-annoying to be installed:
# https://github.com/skorokithakis/django-annoying#readme
# from annoying.fields import AutoOneToOneField

# Create your models here.

def ord_ielts_answer(answer_text):
    if answer_text in ('yes', 'true'):
        return 'a'
    elif answer_text in ('false','no'):
        return 'b'
    else:
        return answer_text

class User(models.Model):
    login = models.CharField(max_length=40, primary_key=True)
    full_name = models.CharField(max_length=150)
    # password = models.CharField(max_length=20)
    rights = models.CharField(max_length=1,
    choices = (('A','Admin'),('S','Student'),('T','Teacher')))
    enc_password = fields.EncryptedCharField(max_length=20, null=True)
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     ## https://github.com/skorokithakis/django-annoying/issues/51
    #     User.student = User.student

    def get_group(self):
        if Student.objects.filter(login=self).exists():
            student = Student.objects.get(login=self)
            return student.group
        else:
            if self.rights == 'A':
                return 'Admin'
            elif self.rights == 'T':
                return 'Teacher'
        return None


class Student(models.Model):
    login = models.OneToOneField(User, primary_key=True,
    on_delete=models.CASCADE)
    group = models.CharField(max_length=20, null=True)


class Quizz(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL,
    null=True)
    name = models.CharField(max_length=30, null=True, unique=True)
    deadline = models.DateTimeField(null=True)
    strip_answers = models.BooleanField(null=True)
    allow_reference = models.BooleanField(default=False)


class Folder(models.Model):
    name = models.CharField(max_length=40, unique=True)


class TestCollection(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def get_activities(self):
        return list(self.ielts_test_set.all()) + list(self.ieltswritingtask_set.all())

class IELTS_Test(models.Model):
    name = models.CharField(max_length=40, unique=True)
    full_grade = models.FloatField(null=True)
    deadline = models.DateTimeField(null=True)
    collection = models.ManyToManyField(TestCollection, blank=True)

    def activity_type(self):
        return 'IELTS_Test'

class Section(models.Model):
    ielts_test = models.ManyToManyField(IELTS_Test, blank=True)
    text = models.TextField()
    section_type = models.CharField(max_length=1,
    choices = (('L', 'Listening'), ('R', "Reading"), ("W", "Writing")), null=True)
    supplement = models.FileField(null=True)
    # upload_to=settings.MEDIA_ROOT
    name = models.CharField(max_length=100, null=True)
    # supplement_type = models.CharField(max_length=1,
    # choices=(('p','pdf'), ('i','image'), ('a','audio')), null=True)



class Question(models.Model):
    quiz = models.ManyToManyField(Quizz, blank=True)
    question_text = models.CharField(max_length=1000)
    ## Question types:
    ##
    ## short_answer - type answer in a special field
    ## multiple_choice - select option from a set
    ##
    ## ielts_question - ielts with short answer
    ## ielts_multiple
    question_type = models.CharField(max_length=20)
    # question_image = models.ImageField(upload_to='supplies/')
    question_level = models.SmallIntegerField()
    error_tag = models.CharField(max_length=45, null=True)
    folder = models.ManyToManyField(Folder, blank=True)
    section = models.ForeignKey(Section, null=True, on_delete=models.SET_NULL)
    case_insensitive = models.BooleanField(default=False)

    ## Whether more than 1 field should be present in the answer sheet for this question:
    multi_field = models.BooleanField(default=False)
    # folder_addr = models.CharField(max_length=45, null=True)
    # essay_addr = models.CharField(max_length=45, null=True)
    # question_group = models.CharField(max_length=45, null=True)


    ## special fields for retrieving previously created questions:
    ukey = models.CharField(max_length=100, null=True) # batch id
    batch_elem_id = models.IntegerField(null = True) # id in batch


    def get_answers(self):
        # print("called")
        wronganswers = self.wronganswer_set.all()
        if wronganswers:
            right_answers = list(self.answer_set.all())
            wrong_answers = list(wronganswers)
            answers = right_answers + wrong_answers
            if self.question_type in ('ielts_multiple','ielts_question'):
                answers = sorted(answers, key=lambda x: ord_ielts_answer(x.answer_text.lower().strip()))
            else:
                shuffle(answers)
            return answers
        else:
            return None
        # return ["method called"]
    
    def get_wrong_answers_text(self):
        wronganswers = self.wronganswer_set.all()
        return ';'.join([i.answer_text for i in wronganswers])
    
    def get_right_answers_text(self):
        if self.multi_field:
            return self.answer_set.all()[0].answer_text
        else:
            rightanswers = self.answer_set.all()
            return ';'.join([i.answer_text for i in rightanswers])
    
    def get_generated_distractors(self):
        if self.question_type == 'multiple_choice':
            return (wanswer.answer_text for wanswer in self.wronganswer_set.all() if wanswer.is_generated)
        return ()
    
    def get_extra_answers(self):
        if self.multi_field:
            return list(enumerate(self.answer_set.all()))[1:]
        else:
            return []
    
    def field_range(self):
        if self.multi_field:
            return range(len(self.answer_set.all()))
        else:
            return 1


class Answer(models.Model):
    question_id = models.ForeignKey(Question,
    on_delete=models.CASCADE, null=True)
    answer_text = models.CharField(max_length=300)


class WrongAnswer(models.Model):
    question = models.ForeignKey(Question,
    on_delete=models.CASCADE, null=True)
    answer_text = models.CharField(max_length=300)
    is_generated = models.BooleanField(default=False)
    distractor_model = models.CharField(max_length=20, null=True)


class Results(models.Model):
    student = models.ForeignKey(User,
    on_delete=models.CASCADE)
    quizz = models.ForeignKey(Quizz, null=True,
    on_delete=models.CASCADE)
    question = models.ForeignKey(Question,
    on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    mark = models.FloatField()


class IELTSWritingTask(models.Model):
    name = models.CharField(max_length=40,unique=True)
    text = models.CharField(max_length=100000,null=True)
    supplement = models.FileField(null=True)
    deadline = models.DateTimeField(null=True)
    collection = models.ManyToManyField(TestCollection, blank=True)

    def activity_type(self):
        return 'IELTSWritingTask'


class IELTSWritingResponse(models.Model):
    task = models.ForeignKey(IELTSWritingTask,
    on_delete=models.CASCADE)
    student = models.ForeignKey(User,
    on_delete=models.CASCADE)
    mark = models.FloatField(null=True)
    text = models.CharField(max_length=50000,null=True)
    submission_dt = models.DateTimeField(null=True)