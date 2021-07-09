from django.db import models


class Contact(models.Model):

    ROLE_CHOICES = (
        ('system_admin', '系統管理員'),
        ('organization_admin', '計畫總管理人'),
        ('project_admin', '個別計畫承辦人'),
        ('uploader', '資料上傳者'),
        ('general', '一般使用者'),
    )
    name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000, blank=True, null=True)
    orcid = models.CharField(max_length=1000, blank=True, null=True)
    role = models.CharField(max_length=1000, choices=ROLE_CHOICES, null=True, blank=True)
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return '<Contact {}> {}'.format(self.id, self.name)

class Organization(models.Model):
    name = models.CharField(max_length=1000)
    projects = models.ManyToManyField('Project')

    def __str__(self):
        return '<Organization {}> {}'.format(self.id, self.name)

class Project(models.Model):

    # projectName
    name = models.CharField('計劃名稱', max_length=1000)

    #OrganizationName
    # projectObjectives
    description = models.TextField(default='', blank=True)

    start_date = models.DateField('計劃時間-開始', null=True, blank=True)
    end_date = models.DateField('計劃時間-結束', null=True, blank=True)

    ## Project People
    #principalInvestigator
    principal_investigator = models.CharField('計劃主持人', max_length=1000, blank=True, null=True)
    funding_agency = models.CharField(max_length=1000, blank=True, null=True)
    region = models.CharField(max_length=1000, blank=True, null=True)
    note = models.CharField(max_length=1000, blank=True, null=True)
    #publishDate
    created = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)
    mode = models.CharField(max_length=4, blank=True, null=True)
    members = models.ManyToManyField('Contact', )
    def __str__(self):
        return '<Project {}>'.format(self.name)

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

class StudyArea(models.Model):
    name = models.CharField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='studyareas')
    created = models.DateTimeField(auto_now_add=True)

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

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    #cameraDeploymentBeginDateTime
    #cameraDeploymentEndDateTime
    longitude = models.DecimalField(decimal_places=8, max_digits=11, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=10, null=True, blank=True)
    altitude = models.SmallIntegerField(null=True, blank=True)
    #deploymentLocationID
    name = models.CharField(max_length=1000)
    #cameraStatus
    camera_status = models.CharField(max_length=4, default='1', choices=CAMERA_STATUS_CHOICES)
    study_areas = models.ManyToManyField(StudyArea, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)


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


    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    file_url = models.CharField(max_length=1000, null=True)
    filename = models.CharField(max_length=1000) # first file if is_sequence
    #dateTimeCaptured
    datetime = models.DateTimeField(null=True)
    #photoType
    photo_type = models.CharField(max_length=100, null=True, choices=PHOTO_TYPE_CHOICES)
    #photoTypeIdentifiedBy
    count = models.PositiveSmallIntegerField(default=1)
    species = models.CharField(max_length=1000, default='', blank=True)
    #taxon = models
    source_data = models.JSONField(default=dict, blank=True)
    sequence = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True) # imageid
    sequence_definition = models.CharField(max_length=1000, default='', blank=True)
    life_stage = models.CharField(max_length=1000, default='', blank=True)
    sex = models.CharField(max_length=1000, default='', blank=True)
    remarks = models.TextField(default='', blank=True)
    animal_id = models.CharField(max_length=1000, default='', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    annotation = models.JSONField(default=dict, blank=True)
    memo = models.TextField(default='', blank=True)
    image_hash = models.TextField(default='', blank=True)
