# Generated by Django 3.0.6 on 2020-05-23 12:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0026_user_enc_password'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='password',
        ),
    ]
