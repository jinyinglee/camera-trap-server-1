# Generated by Django 3.2.12 on 2022-02-17 07:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0066_merge_0065_auto_20220209_0919_0065_deploymentstat'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='file_path',
        ),
        migrations.CreateModel(
            name='ImageFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folder_name', models.CharField(blank=True, default='', max_length=1000)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
    ]