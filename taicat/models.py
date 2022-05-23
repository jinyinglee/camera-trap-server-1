from pathlib import Path
from datetime import (
    timedelta,
    datetime,
    date,
)
import time
from calendar import (
    monthrange,
    monthcalendar
)
import json

from django.db import models
from django.db import connection  # for executing raw SQL
from django.db.models import (
    Q,
    Max,
    Min,
    Count,
)
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.postgres.indexes import GinIndex
from django.conf import settings
from django.core.cache import cache


def find_the_gap(year, array):
    # print (year, array,'----')
    gap_list = []
    gap_list_date = []
    has_gap = False
    if array[0] == 0:
        gap_list.append([0, None])
        has_gap = True

    for i, v in enumerate(array[1:]):
        if has_gap and v == 1:
            gap_list[-1][1] = i
            has_gap = False
        elif not has_gap and v == 0:
            gap_list.append([i+1, None])
            has_gap = True

    if len(gap_list) and gap_list[-1][1] == None:
        gap_list[-1][1] = len(array) - 1

    for x in gap_list:
        gap_list_date.append([
            (datetime(year, 1, 1) + timedelta(days=x[0])).strftime('%Y-%m-%d'),
            (datetime(year, 1, 1) + timedelta(days=x[1])).strftime('%Y-%m-%d'),
        ])
    return gap_list_date


class Species(models.Model):
    DEFAULT_LIST = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                    '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']
    name = models.CharField(max_length=1000, db_index=True)
    count = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    status = models.CharField(max_length=4, default='', null=True, blank=True, db_index=True)  # I: initial

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Contact(models.Model):
    name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000, blank=True, null=True)
    orcid = models.CharField(max_length=1000, blank=True, null=True, unique=True)
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    # is_login = models.BooleanField('登入狀態', default=True)
    is_organization_admin = models.BooleanField('是否為計畫總管理人', default=False)
    # is_forestry_bureau = models.BooleanField('是否能進入林務局管考系統', default=False)
    is_system_admin = models.BooleanField('是否為系統管理員', default=False)

    def __str__(self):
        return '<Contact {}> {}'.format(self.id, self.name)


class ProjectMember(models.Model):
    ROLE_CHOICES = (
        #('system_admin', '系統管理員'),
        #('organization_admin', '計畫總管理人'),
        ('project_admin', '個別計畫承辦人'),
        ('uploader', '資料上傳者'),
        #('general', '一般使用者'),
    )
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    member = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=1000, choices=ROLE_CHOICES, null=True, blank=True)


class Organization(models.Model):
    name = models.CharField(max_length=1000)
    projects = models.ManyToManyField('Project')

    def __str__(self):
        return '<Organization {}> {}'.format(self.id, self.name)


class PublishedProjectManager(models.Manager):
    def get_queryset(self):
        today = timezone.now().date()
        five_years_ago = today - timedelta(days=1825)
        # 5_years_ago = today - timedelta(days=1825) # 365*5
        return super(
            PublishedProjectManager, self).get_queryset().filter(
            Q(publish_date__lte=today) | Q(end_date__lte=five_years_ago))


class Project(models.Model):
    MODE_CHOICES = (
        ('test', '測試'),
        ('official', '正式'),
    )

    # Project Name
    name = models.CharField('計畫名稱', max_length=1000)

    # Project Objectives
    description = models.TextField('計畫摘要', default='', blank=True)
    short_title = models.CharField('計畫簡稱', max_length=1000, blank=True, null=True)
    keyword = models.CharField('計畫關鍵字', max_length=1000, blank=True, null=True)
    start_date = models.DateField('計畫時間-開始', null=True, blank=True)
    end_date = models.DateField('計畫時間-結束', null=True, blank=True)

    # Project People
    executive_unit = models.CharField('執行單位', max_length=100, blank=True, null=True)
    code = models.CharField('計畫編號', max_length=100, blank=True, null=True)
    principal_investigator = models.CharField('計畫主持人', max_length=1000, blank=True, null=True)
    funding_agency = models.CharField('委辦單位', max_length=100, blank=True, null=True)
    region = models.CharField('計畫地區', max_length=1000, null=True, blank=True)
    note = models.CharField('備註', max_length=1000, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)
    mode = models.CharField(max_length=8, blank=True, null=True, default='official', choices=MODE_CHOICES)
    #members = models.ManyToManyField('Contact', )

    # License
    publish_date = models.DateField('公開日期', null=True, blank=True)
    interpretive_data_license = models.CharField('詮釋資料', max_length=10, blank=True, null=True)
    identification_information_license = models.CharField('鑑定資訊', max_length=10, blank=True, null=True)
    video_material_license = models.CharField('影像資料', max_length=10, blank=True, null=True)

    objects = models.Manager()
    published_objects = PublishedProjectManager()
    # OrganizationName

    def __str__(self):
        return '<Project {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def get_deployment_list(self, as_object=False):
        res = []
        sa = self.studyareas.filter(parent__isnull=True).all()
        for i in sa:
            children = []
            for j in StudyArea.objects.filter(parent_id=i.id).all():
                sa_deployments = []
                for x in j.deployment_set.all():
                    item = {
                        'name': x.name,
                        'deployment_id': x.id
                    }
                    if as_object is True:
                        item['object'] = x
                    sa_deployments.append(item)

                children.append({
                    'studyarea_id': j.id,
                    'name': j.name,
                    'deployments': sa_deployments
                })

            deployments = []
            for x in i.deployment_set.all():
                item = {
                    'name': x.name,
                    'deployment_id': x.id
                }
                if as_object is True:
                    item['object'] = x
                deployments.append(item)

            res.append({
                'studyarea_id': i.id,
                'name': i.name,
                'substudyarea': children,
                'deployments': deployments
            })
        return res

    def get_sa_list(self):
        res = []
        sa = self.studyareas.filter().all()
        for i in sa:
            # children = []
            if not i.parent_id:
                res.append({
                    'value': i.id,
                    'label': i.name,
                })
            else:
                parent_name = self.studyareas.get(id=i.parent_id).name
                res.append({
                    'value': i.id,
                    'label': f"{parent_name}_{i.name}",
                })
        return res

    def get_sa_d_list(self):
        res = {}
        sa = self.studyareas.all()
        for i in sa:
            if not i.parent_id:
                res.update({i.name: [{'label': x.name, 'value': x.id} for x in i.deployment_set.all()]})
            else:
                parent_name = self.studyareas.get(id=i.parent_id).name
                res.update({f"{parent_name}_{i.name}": [{'label': x.name, 'value': x.id} for x in i.deployment_set.all()]})
        return res

    def find_and_create_deployment_journal_gap(self, year_list=[]):
        results = []
        if len(year_list) == 0:
            mnx = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(Max('working_end'), Min('working_start'))
            end_year = mnx['working_end__max'].year
            start_year = mnx['working_start__min'].year
            year_list = list(range(start_year, end_year+1))

        for year in year_list:
            deps = self.get_deployment_list(as_object=True)
            for sa in deps:
                items_d = []
                for d in sa['deployments']:
                    dep_id = d['deployment_id']
                    year_stats = []
                    for m in range(1, 13):
                        ret = d['object'].count_working_day(year, m)
                        working_day = ret[0]
                        year_stats += working_day
                    gaps = find_the_gap(year, year_stats)
                    for gap_range in gaps:
                        dj = DeploymentJournal(
                            project_id=self.id,
                            deployment_id=dep_id,
                            studyarea_id=d['object'].study_area_id,
                            working_start=gap_range[0],
                            working_end=gap_range[1],
                            is_effective=False,
                            is_gap=True)
                        dj.save()
                        results.append(dj)
        return results

    def count_deployment_journal(self, year_list=[]):
        years = {}
        if len(year_list) == 0:
            mnx = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(Max('working_end'), Min('working_start'))
            end_year = mnx['working_end__max'].year
            start_year = mnx['working_start__min'].year
            year_list = list(range(start_year, end_year+1))

        for year in year_list:
            year_idx = str(year)
            years[year_idx] = []
            deps = self.get_deployment_list(as_object=True)
            for sa_idx, sa in enumerate(deps):
                items_d = []
                for d_idx, d in enumerate(sa['deployments']):
                    dep_id = d['deployment_id']
                    month_list = []
                    ratio_year = 0
                    year_species_images = d['object'].count_species_images(year)
                    year_stats = []
                    for m in range(1, 13):
                        days_in_month = monthrange(year, m)[1]
                        ret = d['object'].count_working_day(year, m)
                        working_day = ret[0]
                        month_cal = monthcalendar(year, m)
                        count_working_day = sum(working_day)
                        num_images = [0, 0]
                        if yd := year_species_images['species'].get(str(year)):
                            if md := yd.get(str(m)):
                                num_images[0] = md
                        if yd := year_species_images['all'].get(str(year)):
                            if md := yd.get(str(m)):
                                num_images[1] = md
                        data = [
                            year,
                            m,
                            d['name'],
                            count_working_day,
                            days_in_month,
                            month_cal,
                            working_day,
                            ret[1],
                        ]
                        ratio = count_working_day * 100.0 / days_in_month
                        ratio_year += ratio
                        ratio_sp_img = num_images[0] * 100.0/ num_images[1] if num_images[1] > 0 else 0
                        year_stats += working_day
                        month_list.append([ratio, json.dumps(data),  [ratio_sp_img, num_images[0], num_images[1]]])
                    #gaps = find_the_gap(year, year_stats)
                    # move to find_and_create_deployment_journal_gap
                    rows = d['object'].get_deployment_journal_gaps(year)
                    gaps = [{
                        'id': x.id,
                        'idx': x_idx,
                        'caused': x.gap_caused if x.gap_caused else '',
                        'label': '{} - {}'.format(
                            x.working_start.strftime('%m/%d'),
                            x.working_end.strftime('%m/%d'))} for x_idx, x in enumerate(rows)]
                    items_d.append({
                        'name': d['name'],
                        'id': dep_id,
                        'd_idx': d_idx,
                        'items': month_list,
                        'ratio_year': ratio_year / 12.0,
                        'gaps': gaps,
                    })
                years[year_idx].append({
                    'name': sa['name'],
                    'items': items_d,
                    'sa_idx': sa_idx,
                })

        return years

    def count_stats(self):
        start_count = time.time()
        result = Image.objects.filter(project_id=self.id).aggregate(
            Max('datetime'), Min('datetime'))
        result2 = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(
            Max('working_end'), Min('working_start'))

        # deploymeont journal
        deps = self.get_deployment_list(as_object=True)
        end_year = result2['working_end__max'].year
        start_year = result2['working_start__min'].year
        year_list = list(range(start_year, end_year+1))
        data = self.count_deployment_journal(year_list)

        value = {
            'datetime__range': [result['datetime__min'].timestamp(), result['datetime__max'].timestamp()],
            'working__range': [result2['working_start__min'].timestamp(), result2['working_end__max'].timestamp()],
            'updated': time.time(),
            'elapsed': time.time() - start_count,
            'years': data,
        }

        return value

    def get_or_count_stats(self, force=False):
        key = f'project-{self.id}-stats'
        p = Path(f'cache-files/{key}.json')
        if force is False and p.exists():
            # try/except or with not working here, WHY!!
            f = p.open()
            return json.loads(f.read())
        else:
            value = self.count_stats()
            self.write_stats(value)
            return value

    def write_stats(self, data):
        key = f'project-{self.id}-stats'
        f = open(f'cache-files/{key}.json', 'w')
        f.write(json.dumps(data))
        f.close()

class StudyArea(models.Model):
    name = models.CharField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='studyareas')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'<StudyArea {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


# Survey
'''The Survey level includes information on different surveys completed within the same
Project or Study Area. In some cases, a Project or Study Area will consist of more than one
type of Survey. In those cases, the Survey fields can be used to provide information about
each unique Survey. For example, if some aspect of the research or monitoring design
changed during the Project (e.g., the target species or method of data collection) then each
Survey is uniquely identified and the data fields are populated for each unique Survey. Ensure
that each Survey is linked to the appropriate Study Area Name where projects have multiple
Surveys and Study Areas. The Project, Study Area, and Survey may be the same in cases
where surveys were always completed in the same area following the same design. However,
oftentimes surveys with the same methodology, Study Area and Project are separated on a
yearly basis to facilitate annual data submission to WSI. The Survey data is recorded through
the WSI Submissions SharePoint website.'''


class Deployment(models.Model):
    CAMERA_STATUS_CHOICES = (
        ('1', 'Camera Functioning'),
        ('2', 'Unknown Failure'),
        ('3', 'Vandalism/Theft'),
        ('4', 'Memory Card/Film Failure'),
        ('5', 'Camera Hardware Failure'),
        ('6', 'Wildlife Damag'),
    )

    GEODETIC_DATUM_CHOICES = (
        ('TWD97', 'TWD97'),
        ('WGS84', 'WGS84'),
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    # cameraDeploymentBeginDateTime
    # cameraDeploymentEndDateTime
    longitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    altitude = models.SmallIntegerField(null=True, blank=True)
    # deploymentLocationID
    name = models.CharField(max_length=1000)
    # cameraStatus
    camera_status = models.CharField(max_length=4, default='1', choices=CAMERA_STATUS_CHOICES)
    study_area = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)

    geodetic_datum = models.CharField(max_length=10, default='TWD97', choices=GEODETIC_DATUM_CHOICES)
    landcover = models.CharField('土地覆蓋類型', max_length=1000, blank=True, null=True)
    vegetation = models.CharField('植被類型', max_length=1000, blank=True, null=True)
    verbatim_locality = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return f'<Deployment {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'altitude': self.altitude,
        }

    def count_working_day(self, year, month):
        '''計算相機工作時數
        根據 DeploymentJournal 記錄
        '''
        num_month = monthrange(year, month)[1]
        month_start = make_aware(datetime(year, month, 1))
        month_end = make_aware(datetime(year, month, num_month))
        month_stat = [0] * num_month

        query = DeploymentJournal.objects.filter(
            is_effective=True,
            deployment_id=self.id,
            working_start__lte=month_end,
            working_end__gte=month_start).order_by('working_start')

        ret = []
        for i in query.all():
            # updated
            #print ('-------')
            #print (i.working_start.toordinal(), i.working_end.toordinal(), dt1.toordinal(), dt2.toordinal())
            month_stat_part = [0] * num_month
            overlap_range = [max(i.working_start, month_start), min(i.working_end, month_end)]
            gap_days = (overlap_range[0]-month_start).days
            duration_days = (overlap_range[1]-overlap_range[0]).days+1
            for index, stat in enumerate(month_stat):
                if index >= gap_days and index < gap_days + duration_days:
                    month_stat[index] = 1
                    month_stat_part[index] = 1

            ret.append([i.working_start.strftime('%Y-%m-%d'), i.working_end.strftime('%Y-%m-%d')])

        return month_stat, ret

    # cache moved to cache-files
    # def get_species_images(self, year):
    #     key = f'SPIMG_{self.id}_{year}'
    #     if value:= cache.get(key):
    #         # print('cache', key)
    #         return json.loads(value)
    #     else:
    #         value = self.count_species_images(year)
    #         # print('count', value)
    #         cache.set(key, json.dumps(value), 8640000) # 100 d
    #         return value

    def count_species_images(self, year):
        '''計算該年有物種的照片數/全部照片數
        '''
        key = f'SPIMG_{self.id}_{year}'

        with connection.cursor() as cursor:
            q_all = f"SELECT count(distinct image_uuid), \
            DATE_part('year', datetime) as year, \
            DATE_part('month', datetime) as month \
            FROM taicat_image \
            WHERE deployment_id = {self.id} AND DATE_part('year', datetime) = {year} \
            GROUP BY year, DATE_part('month', datetime) \
            ORDER BY year, month;"

            cursor.execute(q_all)
            res = cursor.fetchall()

            by_year_month_all = {}
            for i in res:
                n = i[0]
                year = str(int(i[1]))
                month = str(int(i[2]))
                if year not in by_year_month_all:
                    by_year_month_all[year] = {}

                by_year_month_all[year][month] = n

            q_sp = f"SELECT count(distinct image_uuid), \
            DATE_part('year', datetime) as year, \
            DATE_part('month', datetime) as month \
            FROM taicat_image \
            WHERE deployment_id = {self.id} AND DATE_part('year', datetime) = {year} AND species !='' \
            GROUP BY year, DATE_part('month', datetime) \
            ORDER BY year, month;"
            cursor.execute(q_sp)
            res = cursor.fetchall()
            by_year_month_sp = {}
            for i in res:
                n = i[0]
                year = str(int(i[1]))
                month = str(int(i[2]))
                if year not in by_year_month_sp:
                    by_year_month_sp[year] = {}

                by_year_month_sp[year][month] = n

            return {
                'all': by_year_month_all,
                'species': by_year_month_sp
            }
    def get_deployment_journal_gaps(self, year):
        query = DeploymentJournal.objects.filter(
            is_gap=True,
            deployment_id=self.id,
            working_start__year__gte=year,
            working_end__year__lte=year)
        rows = query.all()
        #print (self.name, year, rows)
        return rows


class Image(models.Model):
    '''if is_sequence, ex: 5 Images, set last 4 Images's is_sequence to True (wouldn't  count)'''
    PHOTO_TYPE_CHOICES = (
        ('start', 'Start'),
        ('end', 'End'),
        ('set-up', 'Set Up'),
        ('blank', 'Blank'),
        ('animal', 'Animal'),
        ('staff', 'Staff'),
        ('unknown', 'Unknown'),
        ('unidentifiable', 'Unidentifiable'),
        ('time-lapse', 'Timelapse'),
    )
    id = models.BigAutoField(primary_key=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True, related_name='images')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    # be careful, this field has no underline!
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    file_url = models.CharField(max_length=1000, null=True)
    filename = models.CharField(max_length=1000)  # first file if is_sequence
    # dateTimeCaptured
    datetime = models.DateTimeField(null=True, db_index=True)
    # photoType
    photo_type = models.CharField(max_length=100, null=True, choices=PHOTO_TYPE_CHOICES)
    # photoTypeIdentifiedBy
    count = models.PositiveSmallIntegerField(default=1, db_index=True)
    species = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    #taxon = models
    sequence = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # imageid
    sequence_definition = models.CharField(max_length=1000, default='', null=True, blank=True)
    annotation_seq = models.PositiveSmallIntegerField(default=0, null=True)
    life_stage = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    sex = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    antler = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    remarks = models.TextField(default='', null=True, blank=True, db_index=True)
    animal_id = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    # mongoDB的自填欄位
    remarks2 = models.JSONField(default=dict, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)
    annotation = models.JSONField(default=dict, blank=True, db_index=True)
    memo = models.TextField(default='', blank=True)
    image_hash = models.TextField(default='', blank=True)
    from_mongo = models.BooleanField(default=False, blank=True)
    # file_path = models.TextField(default='', blank=True)  # deprecated
    image_uuid = models.CharField(max_length=1000, default='', blank=True, null=True, db_index=True)
    has_storage = models.CharField('實體檔案(有無上傳)', max_length=2, default='Y', blank=True) # Y/N or 如果之後有其他種狀況, 如: 存在別的圖台?
    source_data = models.JSONField(default=dict, blank=True)
    exif = models.JSONField(default=dict, blank=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True, db_index=True)
    specific_bucket = models.CharField(max_length=1000, default='', blank=True) # 跟預設不同的 bucket
    deployment_journal = models.ForeignKey('DeploymentJournal', on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的

    def get_associated_media(self, thumbnail='m'):
        bucket_name = settings.AWS_S3_BUCKET
        if self.specific_bucket:
            bucket_name = specific_bucket
        return f'https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{self.image_uuid}-{thumbnail}.jpg'

    @property
    def species_list(self):
        return [x['species'] for x in self.annotation if isinstance(x, dict) and x.get('species', '')]

    def to_dict(self):
        return {
            'id': self.id,
            'species': self.species,
            'filename': self.filename,
            'datetime': self.datetime,
            'project__name': self.project.name if self.project else None,
            'studyarea__name': self.studyarea.name if self.studyarea_id else None,
            'deployment__name': self.deployment.name if self.deployment_id else None,
        }

    class Meta:
        ordering = ['created']
        indexes = [GinIndex(fields=['annotation'])]


class DeletedImage(models.Model):
    '''if is_sequence, ex: 5 Images, set last 4 Images's is_sequence to True (wouldn't  count)'''
    PHOTO_TYPE_CHOICES = (
        ('start', 'Start'),
        ('end', 'End'),
        ('set-up', 'Set Up'),
        ('blank', 'Blank'),
        ('animal', 'Animal'),
        ('staff', 'Staff'),
        ('unknown', 'Unknown'),
        ('unidentifiable', 'Unidentifiable'),
        ('time-lapse', 'Timelapse'),
    )
    id = models.BigAutoField(primary_key=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    file_url = models.CharField(max_length=1000, null=True)
    filename = models.CharField(max_length=1000)  # first file if is_sequence
    datetime = models.DateTimeField(null=True, db_index=True)
    photo_type = models.CharField(max_length=100, null=True, choices=PHOTO_TYPE_CHOICES)
    count = models.PositiveSmallIntegerField(default=1, db_index=True)
    species = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    sequence = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # imageid
    sequence_definition = models.CharField(max_length=1000, default='', blank=True)
    annotation_seq = models.PositiveSmallIntegerField(default=0, null=True)
    life_stage = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    sex = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    antler = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    remarks = models.TextField(default='', null=True, blank=True, db_index=True)
    animal_id = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    remarks2 = models.JSONField(default=dict, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)
    annotation = models.JSONField(default=dict, blank=True, db_index=True)
    memo = models.TextField(default='', blank=True)
    image_hash = models.TextField(default='', blank=True)
    from_mongo = models.BooleanField(default=False, blank=True)
    image_uuid = models.CharField(max_length=1000, default='', blank=True, null=True, db_index=True)
    source_data = models.JSONField(default=dict, blank=True)
    exif = models.JSONField(default=dict, blank=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True, db_index=True)
    has_storage = models.CharField('實體檔案(有無上傳)', max_length=2, default='Y', blank=True) # Y/N or 如果之後有其他種狀況, 如: 存在別的圖台?
    specific_bucket = models.CharField(max_length=1000, default='', blank=True) # 跟預設不同的 bucket
    deployment_journal = models.ForeignKey('DeploymentJournal', on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的

    @property
    def species_list(self):
        return [x['species'] for x in self.annotation if isinstance(x, dict) and x.get('species', '')]

    class Meta:
        ordering = ['created']


class Image_info(models.Model):
    '''
    手動加上 primary key id:
    ALTER TABLE taicat_image_info ADD COLUMN id SERIAL PRIMARY KEY;
    '''
    # image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    id = models.BigAutoField(primary_key=True)
    image_uuid = models.CharField(max_length=1000, default='')
    source_data = models.JSONField(default=dict, blank=True)
    exif = models.JSONField(default=dict, blank=True)


class HomePageStat(models.Model):
    count = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    type = models.CharField(max_length=10, null=True, blank=True)


class ProjectStat(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    num_sa = models.IntegerField(null=True, blank=True)
    num_deployment = models.IntegerField(null=True, blank=True)
    num_data = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    latest_date = models.DateTimeField(null=True, db_index=True)
    earliest_date = models.DateTimeField(null=True, db_index=True)


class ProjectSpecies(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=1000, db_index=True)
    count = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)


class DeploymentJournal(models.Model):
    GAP_CHOICES = (
        '道路中斷 / 路況不佳無法回收',
        '相機遭竊',
        '相機遭刻意破壞',
        '樣點暫時撤除',
        '樣點永久撤除',
        '樣點尚未架設',
        '樣點剛架設尚未回收資料',
        '相機故障',
        '記憶卡故障',
        '記憶卡遺失',
        '電池沒電',
        '其他(自由填寫)',
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    working_start = models.DateTimeField(null=True, blank=True)
    working_end = models.DateTimeField(null=True, blank=True)
    working_unformat = models.CharField(max_length=1000, null=True, blank=True)
    is_effective = models.BooleanField('是否有效', default=True)
    is_gap = models.BooleanField('缺失', default=False)
    gap_caused = models.CharField('缺失原因', max_length=1000, null=True, blank=True)
    folder_name = models.CharField(max_length=1000, null=True, blank=True, default='')
    local_source_id = models.CharField(max_length=1000, null=True, blank=True, default='') # client local database (sqlite)'s folder id, 用來檢查是否上傳過
    created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(null=True, auto_now_add=True)

    @property
    def display_range(self):
        return '{}/{}'.format(self.working_start.strftime('%Y-%m-%d'), self.working_end.strftime('%Y-%m-%d'))

class DeploymentStat(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    year = models.SmallIntegerField(null=True, blank=True)
    month = models.SmallIntegerField(null=True, blank=True)
    count_working_hour = models.SmallIntegerField(null=True, blank=True)
    session = models.CharField(max_length=50, null=True)


class ImageFolder(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True)
    folder_last_updated = models.DateTimeField(null=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)
