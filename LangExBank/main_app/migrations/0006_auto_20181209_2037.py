# Generated by Django 2.1.3 on 2018-12-09 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0005_auto_20181206_2228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='results',
            name='answer',
            field=models.CharField(max_length=100),
        ),
    ]