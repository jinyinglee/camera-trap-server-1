# Generated by Django 4.0.4 on 2022-06-01 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0014_studyareastat'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='deprecated',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
