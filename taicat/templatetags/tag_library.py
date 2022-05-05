# templatetags/tag_library.py
# https://stackoverflow.com/a/15820445/644070

import re

from django import template
from base.models import UploadNotification
from django.utils.safestring import mark_safe

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
        dj = n.upload_history.deployment_journal
        results += f"""
        <div class="notification-item">
        <div class="notification-item-content">
            <div class='notification-item-date'>{n.created.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="notification-item-message"> 
                「{dj.project.name} > {dj.studyarea.name} > {dj.deployment.name} > {dj.folder_name}」上傳狀態為：<strong>{status_map[n.upload_history.status]}</strong>
            </div>
        </div>
        </div>
        """
    return mark_safe(results)


