# Generated by Django 2.2.2 on 2019-11-23 22:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0018_auto_20191123_2102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='results',
            name='quizz',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.Quizz'),
        ),
    ]