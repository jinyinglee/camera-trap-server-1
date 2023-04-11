# Generated by Django 4.0.4 on 2023-03-28 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0023_parametercode'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametercode',
            name='parametername',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='參數名稱'),
        ),
        migrations.AlterField(
            model_name='parametercode',
            name='name',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='參數中文名稱'),
        ),
    ]