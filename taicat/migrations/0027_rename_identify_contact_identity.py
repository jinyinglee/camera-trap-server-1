# Generated by Django 4.0.4 on 2023-03-31 01:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0026_contact_identify_alter_parametercode_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='identify',
            new_name='identity',
        ),
    ]
