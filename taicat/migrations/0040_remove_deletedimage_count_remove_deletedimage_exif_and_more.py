# Generated by Django 4.0.4 on 2023-09-01 05:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0039_remove_homepagestat_type_alter_parametercode_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deletedimage',
            name='count',
        ),
        migrations.RemoveField(
            model_name='deletedimage',
            name='exif',
        ),
        migrations.RemoveField(
            model_name='deletedimage',
            name='photo_type',
        ),
        migrations.RemoveField(
            model_name='deletedimage',
            name='sequence',
        ),
        migrations.RemoveField(
            model_name='deletedimage',
            name='sequence_definition',
        ),
        migrations.RemoveField(
            model_name='deployment',
            name='calculation_data',
        ),
        migrations.RemoveField(
            model_name='image',
            name='count',
        ),
        migrations.RemoveField(
            model_name='image',
            name='exif',
        ),
        migrations.RemoveField(
            model_name='image',
            name='photo_type',
        ),
        migrations.RemoveField(
            model_name='image',
            name='sequence',
        ),
        migrations.RemoveField(
            model_name='image',
            name='sequence_definition',
        ),
    ]
