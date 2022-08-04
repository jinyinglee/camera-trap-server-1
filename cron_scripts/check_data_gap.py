import datetime

from django.core.mail import send_mail
from django.conf import settings

from taicat.utils import half_year_ago, get_project_member
from taicat.models import (
    DeploymentJournal,
    Contact,
)
from base.models import (
    UploadNotification,
)


now = datetime.datetime.now()

# test
# range_list = half_year_ago(2017, 6)

range_list = half_year_ago(now.year, now.month)

# +BEGIN_220728
# 重新判斷未填原因的空缺列表
#rows = DeploymentJournal.objects.filter(
#    is_gap=True,
#    working_end__gt=range_list[0],
#    working_start__lt=range_list[1]
#).filter(Q(gap_caused__exact='') | Q(gap_caused__isnull=True)).all()
rows = DeploymentJournal.objects.filter(
    is_gap=False,
    working_end__gt=range_list[0],
    working_start__lt=range_list[1]
).all()

todo = []
for dj in rows:
    tmp = dj.project.count_deployment_journal([dj.working_start.year])
    info = tmp[str(dj.working_start.year)]
    for sa in info:
        for d in sa['items']:
            for gap in d['gaps']:
                text = gap.get('caused', '')
                if text == '':
                    if dj not in todo:
                        todo.append(dj)
# +END_220728

# send notification to each project members
# TODO: email project membor 權限?
notify_roles = ['project_admin', 'organization_admin']

projects = {}
for dj in todo:
    pid = dj.project_id
    if pid not in projects:
        project_members = get_project_member(pid)
        projects[pid] = {
            'name': dj.project.name,
            'gaps': [],
            'emails': [x.email for x in Contact.objects.filter(id__in=project_members)],
            'members': project_members
        }
    projects[pid]['gaps'].append(f'{dj.deployment.name}: {dj.display_range}')

for project_id, data in projects.items():
    email_subject = '[臺灣自動相機資訊系統] | {} | 資料缺失: 尚未填寫列表'.format(data['name'])
    email_body = '相機位置 缺失區間\n==========================\n' + '\n'.join(data['gaps'])

    # create notification
    for m in data['members']:
        # print (m.id, m.name)
        un = UploadNotification(
            contact_id = m,
            category='gap',
            project_id = project_id
        )
        un.save()
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, data['emails'])
