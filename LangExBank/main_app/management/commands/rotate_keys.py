from main_app.models import User
from django.core.management import BaseCommand

class Command(BaseCommand):
    help = "Changes encryption key for users data. Prepend new key and execute this command. After that you may delete the old key"

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            user.save()
