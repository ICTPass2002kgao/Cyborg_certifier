# Generated by Django 4.2.15 on 2024-10-09 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certierApp', '0003_alter_userdocuments_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdocuments',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
    ]