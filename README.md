# LangExBank

LangExBank is an open-source language testing platform that supports:
 - corpus-based grammar and lexical quizzes based on data of <a href="realec.org">REALEC</a> corpus
 - manually created IELTS-like Reading and Listening assignments

# Instruction manual

Prerequisites:
 - Docker
 - Basic terminal knowledge
 - IPython knowledge (for modifying database in interactive shell)


## Table of contents
1. [Installation](#installation)
2. [Creating users](#creating-users)

    2.1. [Creating users with Django-admin](#creating-users-with-django-admin)

    2.2. [Creating users in terminal](#creating-users-in-ipython-terminal)

    2.3. [Creating random users](#creating-random-users)
    
3. [New users registration](#new-users-registration)
4. [Corpus-based quizzes](#corpus-based-quizzes)

   4.1. [Filling exercise bank](#filling-exercise-bank)
   
   4.2. [Creating new quiz](#creating-new-quiz)
   
   4.3. [Editing created quiz](#editing-created-quiz)
   
   4.4. [Previewing and taking a quiz](#previewing-and-taking-a-quiz)
   
   4.5. [Deleting quizzes](#deleting-quizzes)
5. [IELTS-like tests](#ielts-like-tests)

    5.1. [Reading](#reading)
 
    5.2. [Listening](#listening)
    
6. [Reviewing results](#reviewing-results)

    6.1. [Reviewing corpus-based quiz results](#reviewing-corpus-based-quiz-results)
    
    6.2. [Reviewing IELTS-like test results](#reviewing-ielts-like-test-results)

##  Installation
Learner Corpora Laboratory uses Docker to deploy LangExBank.

### In testing environment
To install LangExBank in testing environment clone this repository to your machine and build Docker container from the source code with.

Enter your terminal emulator and type:
```bash
git clone https://github.com/lcl-hse/LangExBank.git
docker build -f ./langexbank/Dockerfile.prod -t langexbank ./langexbank
docker create --name langexbank_1 langexbank
docker start langexbank_1
docker exec langexbank_1 python manage.py migrate
docker exec -p 8000:8000 -e DEBUG=1 SECRET_KEY=please-change-me DJANGO_ALLOWED_HOSTS=* DJANGO_ENCRYPTION_KEYS=please-change-me LANGEXBANK_ENC_KEY=please-change-me LANGEXBANK_ENCODE_USERS=0 LANGEXBANK_OPEN_SIGNUP=1 gunicorn testing_platform.wsgi:application --bind 0.0.0.0:8000 -t 12000
```

Then go to http://localhost:8000 in your web browser to access LangExBank. However, in this mode LangExBank will be accessible only from your computer so your students will not be able to take tests.

### In production environment
To make your LangExBank accessible from the web you will need to follow the following instructions: 

To use LangExBank in testing environment, you will need to create a separate Docker container for a web server app (e.g. nginx, apache etc.) and orchestrate containers with docker-compose command. In this manual we will use nginx as a containerized web server as nginx Dockerfile and configuration are already present in this repository.

First, open your favourite text editor and create a file in the LangExBank folder called <i>env.prod</i>. This file will contain environment variables needed for LangExBank to run in a Docker environment. Fill the file with the following contents (Meaning of every variable will be explained later):
```
# ./LangExBank/env.prod
DEBUG=0
SECRET_KEY=please-change-me
DJANGO_ALLOWED_HOSTS=localhost yoursite.example.com
DJANGO_ENCRYPTION_KEYS=please-change-me
LANGEXBANK_ENC_KEY=please-change-me
LANGEXBANK_ENCODE_USERS=0
LANGEXBANK_OPEN_SIGNUP=1
DJANGO_MEDIA_ROOT=mediafiles
DJANGO_STATIC_ROOT=staticfiles
```
Where:
<table>
<tr>
 <td>
  <code>DEBUG</code>
 </td>
 <td>
  Whether to run Django in debug mode. Only for testing purposes.
 </td>
</tr>
<tr>
 <td>
  <code>DJANGO_ALLOWED_HOSTS</code>
 </td>
 <td>
  Text string separated by spaces. Allowed IPs and domain names for your LangExBank site. For examples, if your LangExBank site runs on <i>yoursite.example.com</i> or on server with IP <i>172.16.254.1</i> change it to <code>localhost yoursite.example.com</code> or <code>localhost 172.16.254.1</code> respectively.
 </td>
</tr>
<tr>
 <td>
  <code>DJANGO_SECRET_KEY</code>
 </td>
 <td>
  Text or byte string, e.g. <b>abcdef1234</b>. Secret key used by Django to encrypt session data. Django will refuse to start if DJANGO_SECRET_KEY is not set.
 </td>
</tr>
<tr>
 <td>
  <code>DJANGO_ENCRYPTION_KEYS</code>
 </td>
 <td>
  Text string (without spaces). Key to encode user passwords. Best generated by <code>secrets.token_hex(32)</code> in Python prompt.
 </td>
</tr>
<tr>
 <td>
  <code>LANGEXBANK_ENC_KEY</code>
 </td>
 <td>
  Text string. Encoding key to be used by LangExBank for encoding usernames while <code>LANGEXBANK_ENCODE_USERS</code> is set to 1, e.g. <code>abcdef1234</code>
 </td>
</tr>
<tr>
 <td>
  <code>LANGEXBANK_ENCODE_USERS</code>
 </td>
 <td>
  Boolean. Whether to enode usernames while displaying test results.
 </td>
</tr>
<tr>
 <td>
  <code>LANGEXBANK_OPEN_SIGNUP</code>
 </td>
 <td>
  Whether to open registration for new users. This option will be later explained in <a href="#new-users-registration">New users registration</a> section.
 </td>
</tr>
<tr>
 <td>
  <code>DJANGO_MEDIA_ROOT</code>
 </td>
 <td>
  String (respective path). Where to store media files (PDFs, audios, videos).
 </td>
</tr>
<tr>
 <td>
  <code>DJANGO_STATIC_ROOT</code>
 </td>
 <td>
  String (respective path). Where to store static files (JS, CSS).
 </td>
</tr>
</table>

Change variables in LangExBank/env.prod to appropriate values. 

Open <i>docker-compose.yml</i> file in your text editor.

Change in
```
ports:
  - 12345:80
depends_on:
  - web
```

"12345" to the port you want to run LangExBank on.

Run the following commands in your terminal emulator:

```bash
cd LangExBank
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --no-input --clear
```

Then navigate to your domain or IP address in your web browser.

## Creating users
LangExBank support three type of users: Admin, Teacher and Student. To start using LangExBank after deploy you will need to create at least 1 admin user.

You can create new users with three different approaches:

### Creating users with django-admin
To add, edit and delete users with Django-Admin web application you need to create a superuser first:
```bash
docker-compose exec web python manage.py createsuperuser
```

Enter new superuser data according to <a href="https://docs.djangoproject.com/en/3.0/intro/tutorial02/#creating-an-admin-user">Django documentation</a>. Then navigate to <i>yoursite.example.com/admin</i> in your web browser and enter your superuser name and password to access database editing. Then in section <b>MAIN_APP</b> section select <i>Users</i> option (please do not confuse it with <i>Users</i> in <b>AUTHENTICATION AND AUTHORIZATION</b> section.  Then click on <b>ADD USER</b> button and input user data, including username, full name, password and rights (Student, Teacher or Admin) and password(<i>Enc passsword</i> field).

### Creating users in IPython terminal
You can create, delete and edit users in Django IPython console. To do this type in your terminal emulator:

```bash
docker-compose exec web python manage.py shell
```

Your terminal will change to IPython console. Then type the following to import LangExBank object-relational database mappings:
```python
from main_app.models import *
```

Now you will be able to create new users like this (<a href="https://docs.djangoproject.com/en/3.0/intro/tutorial02/#playing-with-the-api">Django docs</a>):
```python
u = User(login='admin', enc_password='please-change-me', rights='A', full_name='The Admin Admin'
u.save()
```
where 'A' represents Admin rights, 'S' - Student rights and 'T' - Teacher rights.

To exit IPython session type the following in your terminal:
```python
exit()
```

### Creating random users
You can create random users with LangExBank management command random_users. Type the following in your terminal:
```bash
docker-compose exec web python manage.py random_users -n 100 -r S -s -fn Users.csv
```

The provided arguments to <i>random_users</i> command are explained below:
<table>
 <tr>
  <td>
   <code>-n --number</code>
  </td>
  <td>
   Integer. How many users to create e.g. 100
  </td>
 </tr>
 <tr>
  <td>
   <code>-r --rights</code>
  </td>
  <td>
   What type of rights to give to the newly created users. Possible options: 'A' (Admin), 'S' (Student) or 'T' (Teacher)
  </td>
 </tr>
 <tr>
  <td>
   <code>-s --save</code>
  </td>
  <td>
   Whether to save newly generated users to CSV file.
  </td>
 </tr>
 <tr>
  <td>
   <code>-fn --filename</code>
  </td>
  <td>
   Name of the CSV file where new user logins and passwords will be saved.
  </td>
 </tr>
</table>

CSV file with user data will be save in your Docker container. To transfer it to your host machine type the following in your terminal emulator:
```bash
docker cp testingplatform_web_1:/home/app_web/LangExBank/Users.csv .
```

If the command results with an error replace <i>testingplatform_web_1</i> with your container name. If you want to specify exact location where you want to place Users csv replace the dot with the folder path.

## New users registration
You can allow new students to register on your LangExBank instance using embedded registration view. To enable this set <code>LANGEXBANK_OPEN_SIGNUP</code> to 1 in <i>LangExBank/env.prod</i> file. Then send <i>yoursite.example.com/easy_register</i> to your students. In order to register the students will be asked to type Full Name, Group id, username and password. In current version of LangExBank no e-mail confirmation is required to register.

## Corpus-based quizzes
You can create quizzes from questions imported from REALEC.

### Filling exercise bank
On the LangExBank main page navigate to the <b>Questions</b> panel to access question bank. Click on <b>Add questions from REALEC</b> button at the bottom to navigate to the question import page. At the question import page fill the following fields:

<table>
 <tr>
  <td>Enter path to REALEC folder</td>
  <td>Path to folder in <a href="http://realec.org">REALEC</a> corpus in POSIX format (e.g. <i>/exam/exam2018/</i>)</td>
 </tr>
 <tr>
  <td>Select error tag from REALEC (selector)</td>
  <td>1 or more error tags from REALEC annotation scheme. By default errors with all tags will be included</td>
 </tr>
 <tr>
  <td>Make questions multiple choice (checkbox)</td>
  <td>Whether to generate multiple-choice questions. Currently multiple choice option generation models support only the following types of errors:
<ul>
 <li>Choice of tense</li>
 <li>Prepositions</li>
 <li>Choice of a lexical item</li>
</ul>
</td>
 </tr>
 <tr>
  <td>Create new folder with name (checkbox)</td>
  <td>Whether to create a new folder in LangExBank with recently generated questions.</td>
 </tr>
 <tr>
  <td>Create new folder with name (text field)</td>
  <td>Name for the new folder (if the option <i>Create new folder with name</i> is selected)</td>
 </tr>
</table>

After filling the form click on the <b>Generate questions</b> button. Generating questions may take several minutes especially in the case of multiple choice questions. Then you will be redirected to the <b>Questions</b> panel.

### Creating new quiz
To create new quiz tick the boxes left to questions on <b>Questions</b> panel, enter quiz name in the <b>Quiz name</b> field at the bottom and click on the <b>Create quiz</b> button.

### Editing created quiz
Navigate to the <b>Quizzes</b> panel and select created quiz. You can edit questions and answers to them, add right answers in case of <i>short answer</i> questions and add distractor oprions in case of <i>multiple choice</i> questions. If you made a mistake editing just click <b>Restore to default</b> in question or answer field to restore its text to value from the database. When you are done please click <b>Save changes</b> to apply your changes to quiz.

### Previewing and taking a quiz
To preview a quiz just select <i>Preview</i> option right to quiz name at the <b>Quizzes</b> panel. To share quiz with your students copy URL from your adress bar at the preview page and send it to them. When you are ready click <b>Submit answers</b> at the bottom of the page. Then you will be redirected to the page with your results in quiz.

### Deleting quizzes
To delete a quiz simply navigate to <b>Quizzes</b> panel, find needed quiz and click on <b>Delete</b>.

## IELTS-like tests
You can create tests in IELTS format of Reading and Listening types on <b>IELTS</b> panel. (The following section of manual is yet to be written)

### Reading
To create an exercise of type Reading select <b>Reading</b> option in <b>Section type</b> field

### Listening
To create an exercise of type Listening select <b>Listening</b> option in <b>Section type</b> field

## Reviewing results
The processs of reviewing results is practicully the same for both corpus-based quizzes and IELTS-like tests.

To review results of either a corpus-based test or an IELTS-like test navigate to <b>Quizzes</b> or <b>IELTS</b> panel respectively and click <b>Results</b> right to the name of the needed quiz. Results will be presented in form of a table:

<table>
 <tr>
  <td>Student</td>
  <td>Group</td>
  <td>Mark</td>
  <td></td>
 </tr>
 <tr>
  <td>Student John Johnson</td>
  <td>Group 1</td>
  <td>0.9</td>
  <td>Details</td>
 </tr>
</table>

To review results of a particular student click <b>Details</b> right to the row with his name. Now you will be able to see answers submitted by the student as well as right answers to quiz questions. To edit mark for each question navigate your cursor to mark column and enter new mark in floating point number format (e.g. <i>0.9</i> or <i>2.0</i>. If you think that the answer submotted by a student was correct click <b>Mark as new correct</b> below answer. (Warning: the answer will be counted as correct only for new test takers). Adding new correct answer is not supported for multiple choice questions. When you are done reviewing student results click <b>Save changes</b> at the bottom of the page to apply your changes.
