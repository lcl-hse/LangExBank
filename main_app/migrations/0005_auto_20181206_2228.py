# Generated by Django 2.1.3 on 2018-12-06 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0004_auto_20181205_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizz',
            name='name',
            field=models.CharField(max_length=30, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='group',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
