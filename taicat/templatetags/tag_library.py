# templatetags/tag_library.py
# https://stackoverflow.com/a/15820445/644070

from datetime import timedelta
import re

from django import template
from base.models import UploadNotification,Announcement
from django.utils.safestring import mark_safe
from taicat.models import Organization, ProjectMember, Contact
from django.db.models import Q

register = template.Library()


@register.filter()
def to_int(value):
    return int(value)


@register.simple_tag()
def find_event_num(data, year, month):
    '''
    for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            return i['event_num']
    '''
    return 0


# for calculation
@register.simple_tag()
def find_oi_3(data, year, month):
    '''
    for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            if wh := i['working_hour'][0]:
                return i['image_num'] * 1.0 / wh * 1000
    '''
    return 0


@register.simple_tag()
def find_pod(data, year, month):
    '''for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            if pod := i['pod'][0]:
                return pod
    '''
    return 0


@register.simple_tag()
def find_presence_absence(data, year, month):
    '''
    for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            if pod := i['pod'][0]:
                return 1
    '''
    return 0


@register.filter
def get_value_in_qs(queryset, key):
    return queryset.values_list(key, flat=True)


# https://stackoverflow.com/questions/46247729/django-mark-as-read-notifications
@register.filter
def has_unread_notif(contact_id):
    notifications = UploadNotification.objects.filter(contact_id=contact_id, is_read=False)
    if notifications.exists():
        return True
    return False


status_map = {
    'uploading': '上傳中',
    'finished': '已完成',
    'unfinished': '未完成'
}

@register.filter
def get_notif(contact_id):
    notifications = UploadNotification.objects.filter(contact_id=contact_id).order_by('-created')[:20]
    results = ""
    for n in notifications:
        # 上傳狀態通知
        if n.category == 'upload': 
            created_8 = n.created + timedelta(hours=8)
            dj = n.upload_history.deployment_journal
            results += f"""
            <div class="notification-item">
            <div class="notification-item-content">
                <div class='notification-item-date'>{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div class="notification-item-message"> 
                    「{dj.project.name} > {dj.studyarea.name} > {dj.deployment.name} > {dj.folder_name}」上傳狀態為：<strong>{status_map[n.upload_history.status]}</strong>
                </div>
            </div>
            </div>
            """
        # 資料缺失通知
        elif n.category == 'gap': 
            created_8 = n.created + timedelta(hours=8)
            results += f"""
            <div class="notification-item">
            <div class="notification-item-content">
                <div class='notification-item-date'>{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div class="notification-item-message"> 
                    「{n.project.name}」有缺失資料，請至管考介面填寫缺失原因
                </div>
            </div>
            </div>
            """
    if not results:
        results = """
        <div class="notification-item">
        <div class="notification-item-content">
            <div class="notification-item-message"> 
            暫無通知
            </div>
        </div>
        </div>
        """
    return mark_safe(results)


# 確認是否有權限取得單機版檔案
@register.filter()
def if_desktop(user_id):
    # 系統管理員
    # 計畫總管理人

    projects = list(Organization.objects.get(name='林務局').projects.all().values_list('id',flat=True))
    if ProjectMember.objects.filter(project__in=projects,member_id=user_id).exists():
        return True
    elif Contact.objects.filter(Q(id=user_id, is_organization_admin=True, organization__name='林務局')|Q(id=user_id, is_system_admin=True)).exists():
        return True
    else:
        return False


# 確認是否有權限設定
@register.filter()
def if_permission(user_id):
    # 系統管理員
    if Contact.objects.filter(id=user_id, is_system_admin=True).exists():
        return True
    else:
        return False

@register.filter
def announcement_content (contact_id):
    notifications = Announcement.objects.latest('created').title
        
    return notifications