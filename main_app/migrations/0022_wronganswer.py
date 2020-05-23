# Generated by Django 2.2.2 on 2020-01-20 21:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0021_question_ukey'),
    ]

    operations = [
        migrations.CreateModel(
            name='WrongAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.CharField(max_length=300)),
                ('question_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.Question')),
            ],
        ),
    ]
