# Generated by Django 3.0.6 on 2020-10-05 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0029_auto_20201005_2307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ieltswritingtask',
            name='text',
            field=models.CharField(max_length=100000, null=True),
        ),
    ]