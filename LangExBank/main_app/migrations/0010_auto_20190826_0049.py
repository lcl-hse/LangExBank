# Generated by Django 2.2.2 on 2019-08-25 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0009_auto_20190816_2119'),
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='folder',
            field=models.ManyToManyField(blank=True, to='main_app.Folder'),
        ),
    ]