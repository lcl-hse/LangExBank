# Generated by Django 3.0.6 on 2020-05-23 11:45

from django.db import migrations
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0025_auto_20200522_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='enc_password',
            field=encrypted_fields.fields.EncryptedCharField(max_length=20, null=True),
        ),
    ]
