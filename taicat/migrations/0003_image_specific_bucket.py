# Generated by Django 4.0.4 on 2022-05-03 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0002_image_has_storage'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='specific_bucket',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
    ]
