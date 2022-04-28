# Generated by Django 4.0.4 on 2022-04-27 08:07

import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000)),
                ('email', models.CharField(blank=True, max_length=1000, null=True)),
                ('orcid', models.CharField(blank=True, max_length=1000, null=True, unique=True)),
                ('is_organization_admin', models.BooleanField(default=False, verbose_name='是否為計畫總管理人')),
                ('is_system_admin', models.BooleanField(default=False, verbose_name='是否為系統管理員')),
            ],
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('longitude', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('altitude', models.SmallIntegerField(blank=True, null=True)),
                ('name', models.CharField(max_length=1000)),
                ('camera_status', models.CharField(choices=[('1', 'Camera Functioning'), ('2', 'Unknown Failure'), ('3', 'Vandalism/Theft'), ('4', 'Memory Card/Film Failure'), ('5', 'Camera Hardware Failure'), ('6', 'Wildlife Damag')], default='1', max_length=4)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('source_data', models.JSONField(blank=True, default=dict)),
                ('geodetic_datum', models.CharField(choices=[('TWD97', 'TWD97'), ('WGS84', 'WGS84')], default='TWD97', max_length=10)),
                ('landcover', models.CharField(blank=True, max_length=1000, null=True, verbose_name='土地覆蓋類型')),
                ('vegetation', models.CharField(blank=True, max_length=1000, null=True, verbose_name='植被類型')),
                ('verbatim_locality', models.CharField(blank=True, max_length=1000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='HomePageStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('type', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Image_info',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('image_uuid', models.CharField(default='', max_length=1000)),
                ('source_data', models.JSONField(blank=True, default=dict)),
                ('exif', models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000, verbose_name='計畫名稱')),
                ('description', models.TextField(blank=True, default='', verbose_name='計畫摘要')),
                ('short_title', models.CharField(blank=True, max_length=1000, null=True, verbose_name='計畫簡稱')),
                ('keyword', models.CharField(blank=True, max_length=1000, null=True, verbose_name='計畫關鍵字')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='計畫時間-開始')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='計畫時間-結束')),
                ('executive_unit', models.CharField(blank=True, max_length=100, null=True, verbose_name='執行單位')),
                ('code', models.CharField(blank=True, max_length=100, null=True, verbose_name='計畫編號')),
                ('principal_investigator', models.CharField(blank=True, max_length=1000, null=True, verbose_name='計畫主持人')),
                ('funding_agency', models.CharField(blank=True, max_length=100, null=True, verbose_name='委辦單位')),
                ('region', models.CharField(blank=True, max_length=1000, null=True, verbose_name='計畫地區')),
                ('note', models.CharField(blank=True, max_length=1000, null=True, verbose_name='備註')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('source_data', models.JSONField(blank=True, default=dict)),
                ('mode', models.CharField(blank=True, choices=[('test', '測試'), ('official', '正式')], default='official', max_length=8, null=True)),
                ('publish_date', models.DateField(blank=True, null=True, verbose_name='公開日期')),
                ('interpretive_data_license', models.CharField(blank=True, max_length=10, null=True, verbose_name='詮釋資料')),
                ('identification_information_license', models.CharField(blank=True, max_length=10, null=True, verbose_name='鑑定資訊')),
                ('video_material_license', models.CharField(blank=True, max_length=10, null=True, verbose_name='影像資料')),
            ],
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=1000)),
                ('count', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('status', models.CharField(blank=True, db_index=True, default='', max_length=4, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StudyArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='taicat.studyarea')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='studyareas', to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_sa', models.IntegerField(blank=True, null=True)),
                ('num_deployment', models.IntegerField(blank=True, null=True)),
                ('num_data', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('latest_date', models.DateTimeField(db_index=True, null=True)),
                ('earliest_date', models.DateTimeField(db_index=True, null=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectSpecies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=1000)),
                ('count', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, choices=[('project_admin', '個別計畫承辦人'), ('uploader', '資料上傳者')], max_length=1000, null=True)),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.contact')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000)),
                ('projects', models.ManyToManyField(to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='ImageFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folder_name', models.CharField(blank=True, default='', max_length=1000)),
                ('folder_last_updated', models.DateTimeField(db_index=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('file_url', models.CharField(max_length=1000, null=True)),
                ('filename', models.CharField(max_length=1000)),
                ('datetime', models.DateTimeField(db_index=True, null=True)),
                ('photo_type', models.CharField(choices=[('start', 'Start'), ('end', 'End'), ('set-up', 'Set Up'), ('blank', 'Blank'), ('animal', 'Animal'), ('staff', 'Staff'), ('unknown', 'Unknown'), ('unidentifiable', 'Unidentifiable'), ('time-lapse', 'Timelapse')], max_length=100, null=True)),
                ('count', models.PositiveSmallIntegerField(db_index=True, default=1)),
                ('species', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('sequence_definition', models.CharField(blank=True, default='', max_length=1000, null=True)),
                ('life_stage', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('sex', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('antler', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('remarks', models.TextField(blank=True, db_index=True, default='', null=True)),
                ('animal_id', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('remarks2', models.JSONField(blank=True, default=dict, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('annotation', models.JSONField(blank=True, db_index=True, default=dict)),
                ('memo', models.TextField(blank=True, default='')),
                ('image_hash', models.TextField(blank=True, default='')),
                ('from_mongo', models.BooleanField(blank=True, default=False)),
                ('image_uuid', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('source_data', models.JSONField(blank=True, default=dict)),
                ('exif', models.JSONField(blank=True, default=dict)),
                ('folder_name', models.CharField(blank=True, db_index=True, default='', max_length=1000)),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deployment')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
                ('sequence', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.image')),
                ('studyarea', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='DeploymentStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.SmallIntegerField(blank=True, null=True)),
                ('month', models.SmallIntegerField(blank=True, null=True)),
                ('count_working_hour', models.SmallIntegerField(blank=True, null=True)),
                ('session', models.CharField(max_length=50, null=True)),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deployment')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
                ('studyarea', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea')),
            ],
        ),
        migrations.CreateModel(
            name='DeploymentJournal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('working_start', models.DateTimeField(blank=True, null=True)),
                ('working_end', models.DateTimeField(blank=True, null=True)),
                ('working_unformat', models.CharField(blank=True, max_length=1000, null=True)),
                ('is_effective', models.BooleanField(default=True, verbose_name='是否有效')),
                ('is_gap', models.BooleanField(default=False, verbose_name='缺失記錄')),
                ('gap_caused', models.CharField(blank=True, max_length=1000, null=True)),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deployment')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
                ('studyarea', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea')),
            ],
        ),
        migrations.AddField(
            model_name='deployment',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='study_area',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea'),
        ),
        migrations.CreateModel(
            name='DeletedImage',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('file_url', models.CharField(max_length=1000, null=True)),
                ('filename', models.CharField(max_length=1000)),
                ('datetime', models.DateTimeField(db_index=True, null=True)),
                ('photo_type', models.CharField(choices=[('start', 'Start'), ('end', 'End'), ('set-up', 'Set Up'), ('blank', 'Blank'), ('animal', 'Animal'), ('staff', 'Staff'), ('unknown', 'Unknown'), ('unidentifiable', 'Unidentifiable'), ('time-lapse', 'Timelapse')], max_length=100, null=True)),
                ('count', models.PositiveSmallIntegerField(db_index=True, default=1)),
                ('species', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('sequence_definition', models.CharField(blank=True, default='', max_length=1000)),
                ('life_stage', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('sex', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('antler', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('remarks', models.TextField(blank=True, db_index=True, default='', null=True)),
                ('animal_id', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('remarks2', models.JSONField(blank=True, default=dict, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('annotation', models.JSONField(blank=True, db_index=True, default=dict)),
                ('memo', models.TextField(blank=True, default='')),
                ('image_hash', models.TextField(blank=True, default='')),
                ('from_mongo', models.BooleanField(blank=True, default=False)),
                ('image_uuid', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True)),
                ('source_data', models.JSONField(blank=True, default=dict)),
                ('exif', models.JSONField(blank=True, default=dict)),
                ('folder_name', models.CharField(blank=True, db_index=True, default='', max_length=1000)),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deployment')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
                ('sequence', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deletedimage')),
                ('studyarea', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.AddField(
            model_name='contact',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.organization'),
        ),
        migrations.AddIndex(
            model_name='image',
            index=django.contrib.postgres.indexes.GinIndex(fields=['annotation'], name='taicat_imag_annotat_280c10_gin'),
        ),
    ]
