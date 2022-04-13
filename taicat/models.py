from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex


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
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
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

    def get_deployment_list(self):
        res = []
        sa = self.studyareas.filter(parent__isnull=True).all()
        for i in sa:
            children = []
            for j in StudyArea.objects.filter(parent_id=i.id).all():
                children.append({
                    'studyarea_id': j.id,
                    'name': j.name,
                    'deployments': [{'name': x.name, 'deployment_id': x.id} for x in j.deployment_set.all()]
                })

            res.append({
                'studyarea_id': i.id,
                'name': i.name,
                'substudyarea': children,
                'deployments': [{'name': x.name, 'deployment_id': x.id} for x in i.deployment_set.all()]
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
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
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

    source_data = models.JSONField(default=dict, blank=True)
    exif = models.JSONField(default=dict, blank=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True, db_index=True)

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

    @property
    def species_list(self):
        return [x['species'] for x in self.annotation if isinstance(x, dict) and x.get('species', '')]

    class Meta:
        ordering = ['created']


class Image_info(models.Model):
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
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(
        Deployment, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(
        StudyArea, on_delete=models.SET_NULL, null=True)
    working_start = models.DateTimeField(null=True, blank=True)
    working_end = models.DateTimeField(null=True, blank=True)
    working_unformat = models.CharField(max_length=1000, null=True, blank=True)
    is_effective = models.BooleanField('是否有效', default=True)


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
