from django.contrib import admin

from .models import (
    UploadHistory
)

@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    model = UploadHistory

