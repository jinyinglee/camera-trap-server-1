from django.db import models
from taicat.models import DeploymentJournal, Contact


class UploadHistory(models.Model):
    STATUS_CHOICES = (
        ('uploading', '上傳中'),
        ('finished', '已完成'),
        ('unfinished', '未完成'),
    )
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    species_error = models.BooleanField(default=False, blank=True) # 物種欄位未完整填寫
    upload_error = models.BooleanField(default=False, blank=True) # 影像未成功上傳
    deployment_journal = models.ForeignKey(DeploymentJournal, on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的


class UploadNotification(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    is_read = models.BooleanField(default=False, blank=True)
    upload_history = models.ForeignKey(UploadHistory, on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)

