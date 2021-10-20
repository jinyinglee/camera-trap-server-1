# Generated by Django 3.2.8 on 2021-10-19 08:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0042_image_taicat_imag_annotat_280c10_gin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stat',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('num_image', models.IntegerField(blank=True, default=0, null=True)),
                ('num_deployment', models.IntegerField(blank=True, default=0, null=True)),
                ('s1', models.IntegerField(blank=True, default=0, null=True, verbose_name='水鹿')),
                ('s2', models.IntegerField(blank=True, default=0, null=True, verbose_name='山羌')),
                ('s3', models.IntegerField(blank=True, default=0, null=True, verbose_name='獼猴')),
                ('s4', models.IntegerField(blank=True, default=0, null=True, verbose_name='山羊')),
                ('s5', models.IntegerField(blank=True, default=0, null=True, verbose_name='野豬')),
                ('s6', models.IntegerField(blank=True, default=0, null=True, verbose_name='鼬獾')),
                ('s7', models.IntegerField(blank=True, default=0, null=True, verbose_name='白鼻心')),
                ('s8', models.IntegerField(blank=True, default=0, null=True, verbose_name='食蟹獴')),
                ('s9', models.IntegerField(blank=True, default=0, null=True, verbose_name='松鼠')),
                ('s10', models.IntegerField(blank=True, default=0, null=True, verbose_name='飛鼠')),
                ('s11', models.IntegerField(blank=True, default=0, null=True, verbose_name='黃喉貂')),
                ('s12', models.IntegerField(blank=True, default=0, null=True, verbose_name='黃鼠狼')),
                ('s13', models.IntegerField(blank=True, default=0, null=True, verbose_name='小黃鼠狼')),
                ('s14', models.IntegerField(blank=True, default=0, null=True, verbose_name='麝香貓')),
                ('s15', models.IntegerField(blank=True, default=0, null=True, verbose_name='黑熊')),
                ('s16', models.IntegerField(blank=True, default=0, null=True, verbose_name='石虎')),
                ('s17', models.IntegerField(blank=True, default=0, null=True, verbose_name='穿山甲')),
                ('s18', models.IntegerField(blank=True, default=0, null=True, verbose_name='梅花鹿')),
                ('s19', models.IntegerField(blank=True, default=0, null=True, verbose_name='野兔')),
                ('s20', models.IntegerField(blank=True, default=0, null=True, verbose_name='蝙蝠')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
    ]