# Generated by Django 2.2.2 on 2019-11-21 22:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0014_auto_20191121_2342'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='section',
            name='supplement_type',
        ),
    ]
