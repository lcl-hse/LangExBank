"""testing_platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path

from django.conf import settings
from django.views.static import serve


from django.contrib.auth import views as auth_views


from main_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('generateQuestions/<coll>/<doc>', views.show_generated_questions, name="show_generated_questions"),
    path('accounts/login/', auth_views.LoginView.as_view()),
    path('takeQuiz/<int:quiz_id>', views.display_quiz, name="take_quiz"),
    path('editQuiz/<int:quiz_id>', views.edit_quiz, name="edit_quiz"),
    path('editQuiz/<int:quiz_id>/<int:page_num>', views.edit_quiz, name="edit_quiz"),
    path('login/', views.login, name="login"),
    path('', views.index, name="index"),
    path('quizzes/', views.quiz_list, name="quiz_list"),
    path('questions/', views.display_questions, name="display_questions"),
    path('easy_register/', views.easy_register, name="easy_register"),
    path('grades/<int:quiz_id>', views.quiz_grades, name="quiz_grades"),
    path('grades/<int:quiz_id>/download', views.download_grades, name="download_grades"),
    path('grades/<int:quiz_id>/<str:student_id>', views.student_answers, name="student_answers"),
    path('grades/<int:quiz_id>/<str:student_id>/download', views.download_answers, name="download_answers"),
    path('addQuestions/<int:quiz_id>/', views.add_questions, name="add_questions"),
    path('pdfDemo/', views.pdf_demo, name="pdf_demo"),
    # path('questionContainers/', views.question_containers, name="question_containers"),
    # path('testMediaFolder/', views.test_media_folder, name="test_media_folder"),
    # path('testUploads/', views.test_uploads, name="test_uploads"),
    path('IELTS/', views.ielts_test_list, name="ielts_test_list"),
    path('editIELTS/', views.edit_ielts_test, name="edit_ielts"),
    path('editIELTS/<int:test_id>', views.edit_ielts_test, name="edit_ielts"),
    path('takeIELTSTest/<int:test_id>', views.take_ielts_test, name="take_ielts"),
    path('IELTSgrades/<int:test_id>', views.ielts_grades, name="ielts_grades"),
    path('IELTSgrades/<int:test_id>/<str:student_id>', views.student_test_results, name="student_test_results"),
    path('IELTSgrades/<int:test_id>/<str:student_id>/download', views.download_ielts_results, name="download_ielts_results"),
    path('fromFolder/', views.questions_from_folder, name='questions_from_folder'),
    # path('testAjax/', views.test_ajax, name="test_ajax"),
    path('deleteIELTSTest/', views.delete_test, name="delete_test"),
    path('deleteActivity/', views.delete_activity, name="delete_activity"),
    path('deleteQuiz/', views.delete_quiz, name="delete_quiz"),
    path('distractorReport/<int:quiz_id>', views.distractor_report, name='distractor_report'),
    path('editIELTSWriting/', views.edit_writing, name="edit_writing"),
    path('editIELTSWriting/<str:writing_test_name>', views.edit_writing, name="edit_writing"),
    path('takeIELTSWriting/<str:writing_test_name>', views.take_writing, name="take_writing"),
    path('IELTSWritingGrades/<str:writing_test_name>', views.writing_results, name='writing_results'),
    path('ReviewIELTSWriting/<str:writing_test_name>/<str:student_id>', views.review_writing, name='review_writing'),
    path('editIELTSSpeaking/', views.edit_speaking, name="edit_speaking"),
    path('editIELTSSpeaking/<int:test_id>', views.edit_speaking, name="edit_speaking"),
    path('takeIELTSSpeaking/<int:test_id>', views.take_speaking, name="take_speaking"),
    path('IELTSSpeakingGrades/<int:test_id>', views.speaking_results, name='speaking_results'),
    path('ReviewIELTSSpeaking/<int:test_id>/<str:student_id>', views.review_speaking, name='review_speaking'),
    path('IELTS/Collections/', views.display_test_collections, name="ielts_test_collections"),
    path('deleteCollection/', views.delete_collection, name="delete_collection"),
    path('addTestToCollection/<str:collection_id>', views.add_test_to_collection, name="add_test_to_collection")
]

# path('questions/<str:err_type>', views.display_questions, name="display_questions"),

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]