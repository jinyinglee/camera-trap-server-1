# Generated by Django 3.2.2 on 2021-07-22 09:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0029_rename_members_projectmember_member'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'managed': True},
        ),
        migrations.AlterModelTable(
            name='contact',
            table='contact',
        ),
    ]
