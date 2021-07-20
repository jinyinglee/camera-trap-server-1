# Generated by Django 3.2.2 on 2021-07-19 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0020_auto_20210716_0845'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='is_forestry_bureau',
            field=models.BooleanField(default=False, verbose_name='是否能進入林務局管考系統'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='is_system_admin',
            field=models.BooleanField(default=False, verbose_name='是否為系統管理員'),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='role',
            field=models.CharField(blank=True, choices=[('project_admin', '個別計畫承辦人'), ('uploader', '資料上傳者')], max_length=1000, null=True),
        ),
    ]
