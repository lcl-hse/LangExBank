# LangExBank

LangExBank is an open-source testing platform that supports:
 - corpus-based grammar and lexical quizzes based on data of <a href="realec.org">REALEC</a> corpus
 - manually created IELTS-like Reading and Listening assignments

To use LangExBank you need to configure testing_platform/settings.py as follows:
 - FIELD_ENCRYPTION_KEYS - output of secrets.token_hex(32) in Python prompt
 - encode - whether to encode user names in Results section
 - login_enc_key - key for encrypting user_names
 - registration_open - whether to open registration for new students

If you are deploying LangExBank using Docker you can set environmental variables to needed values inside your container without modifying settings.py

To edit database create superuser in Django-admin with:

python manage.py createsuperuser

And visit http://your-url/admin to create new users.

To add new questions from REALEC visit http://your-url/fromFolder/

To review Question database, visit http://your-url/Questions/

You can filter Questions by tag and type using 'Select question types' and 'Select error tag from REALEC' selectors.

To add new quiz select questions at http://your-url/Questions/, enter quiz name and click 'Add questions from REALEC'.

To enable registration set variable registration_open in testing_platform/settings.py to True or to 1 in your environment and then send link http://your-url/easy_register/ to your students

Before using LangExBank please install required Python packages from requirements.txt
