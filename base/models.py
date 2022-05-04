from django.db import models
from taicat.models import DeploymentJournal


class UploadHistory(models.Model):
    STATUS_CHOICES = (
        ('uploading', '上傳中'),
        ('finished', '已完成'),
        ('unfinished', '未完成'),
    )
    last_updated = models.DateTimeField(null=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    deployment_journal = models.ForeignKey(DeploymentJournal, on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的
