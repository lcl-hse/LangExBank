from main_app.models import User
from main_app.views import mask_user, get_group
from django.core.management import BaseCommand

import pandas as pd

class Command(BaseCommand):
    help = '''Saves user info (full name, login, group, rights)
    to an excel file called Users.xlsx'''

    def handle(self, *args, **kwargs):
        user_data = [{'Full name': user.full_name,
             'Encrypted name': mask_user(user),
             'Login': user.login,
             'Rights': user.rights,
             'Group': get_group(user)} for user in User.objects.all()]
        df = pd.DataFrame(user_data)
        df.to_excel("Users.xlsx")
    