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
