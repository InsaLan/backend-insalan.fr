# Generated by Django 4.1.12 on 2023-11-29 19:07

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='logo',
            field=models.FileField(upload_to='partners', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'svg', 'webp'])], verbose_name='Logo'),
        ),
    ]
