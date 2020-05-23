from main_app.models import User
from django.core.management.base import BaseCommand
from datetime import datetime
# from testing_platform.settings import BASE_DIR

import random
import string
import json

## random string generation taken from
## https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits

def default_fn():
    return 'users'+datetime.now().isoformat().replace(':', '')+'.json'

def random_login():
    return ''.join(random.choices(string.ascii_uppercase, k=2))+''.join(random.choices(string.ascii_lowercase, k=10))

def random_password():
    return ''.join(random.choices(string.ascii_lowercase+string.ascii_uppercase+string.digits, k=20))

def random_capitalised():
    return random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_lowercase, k=10))

def random_name():
    return ' '.join([random_capitalised() for i in range(3)])


class Command(BaseCommand):
    help = 'Fills database with selected amount of randomly generated users'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--number', type=int, help='How many users to create')
        parser.add_argument('-r', '--rights', type=str, help='Which type of rights (A - Admin, T - Teacher, S - Student) created users should have')
        parser.add_argument('-s', '--save', dest='save', action='store_true', help='Save created user list to a CSV file')
        parser.add_argument('-fn', '--filename', type=str, help='Filename for the saved userlist')
    
    def handle(self, *args, **kwargs):
        new_users = [User(login=random_login(), 
                          password=random_password(),
                          full_name=random_name(),
                          rights=kwargs['rights']
                          ) for i in range(kwargs['number'])]
        User.objects.bulk_create(new_users)

        if kwargs['save']:
            if 'filename' in kwargs:
                self.save_users(new_users, fn=kwargs['filename'])
            else:
                self.save_users(new_users)
    
    def save_users(self, users, fn=None):
        userlist = [{"login": u.login, "password": u.password} for u in users]

        if not fn:
            fn = default_fn()

        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(userlist, f)