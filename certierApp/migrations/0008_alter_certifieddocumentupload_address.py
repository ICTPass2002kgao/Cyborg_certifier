# Generated by Django 4.2.15 on 2024-11-26 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certierApp', '0007_certifieddocumentupload_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certifieddocumentupload',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]