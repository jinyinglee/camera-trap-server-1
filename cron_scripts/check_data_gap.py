import datetime

from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count

from taicat.utils import half_year_ago, get_project_member
from taicat.models import (
    DeploymentJournal,
    Contact,
    Project,
)
from base.models import (
    UploadNotification,
)


now = datetime.datetime.now()

# test
# range_list = half_year_ago(2017, 6)

range_list = half_year_ago(now.year, now.month)
rows = DeploymentJournal.objects.values_list('project_id', 'working_start__year').annotate(total=Count('id')).filter(working_end__gt=range_list[0], working_start__lt=range_list[1]).all()

for i in rows:
    project_id = i[0]
    year = i[1]
    proj = Project.objects.get(pk=project_id)
    data = proj.count_deployment_journal([year])


    output = {'count': 0, 'studyareas': {}}
    for sa in data[str(year)]:
        # body += '\n\n# 樣區名稱: {}\n'.format(sa['name'])
        #sa_title = '\n\n# 樣區名稱: {}\n'.format(sa['name'])
        sa_output = {'count': 0, 'deployments': {}}
        for dep in sa['items']:
            #dep_title = '\n## 相機位置: {}\n'.format(dep['name'])
            for gap in dep['gaps']:
                gap_start = datetime.datetime.fromtimestamp(gap['range'][0])
                gap_end = datetime.datetime.fromtimestamp(gap['range'][1])
                #print(range_list, gap_start, gap_end)
                if 1: #gap_end >= range_list[0] and gap_end <= range_list[1]:
                    if dep['id'] not in sa_output['deployments']:
                        sa_output['deployments'][dep['id']] = {
                            'count': 0,
                            'items': [],
                            'name': dep['name']
                        }

                    gap_title = '* {}/{}\n'.format(gap_start.strftime('%Y-%m-%d'), gap_end.strftime('%Y-%m-%d'))
                    sa_output['deployments'][dep['id']]['items'].append(gap_title)
                    sa_output['deployments'][dep['id']]['count'] += 1
                    sa_output['count'] += 1

            output['count'] += sa_output['count']
            output['studyareas'][sa['name']] = sa_output['deployments']

    # print(output)

    email_subject = '[臺灣自動相機資訊系統] | {} | 資料缺失: 尚未填寫列表'.format(proj.name)
    email_body = '資料缺失: 尚未填寫列表\n----------------------'
    if output['count'] > 0 :
        for sa_name in output['studyareas']:
            email_body += '\n\n# 樣區名稱: {}\n'.format(sa_name)
            for _, d in output['studyareas'][sa_name].items():
                email_body += '\n## 相機位置: {}\n'.format(d['name'])
                for x in d['items']:
                    email_body += x
    else:
        email_body += '\n目前無資料缺失。'

    project_members = get_project_member(project_id)
    email_list = [x.email for x in Contact.objects.filter(id__in=project_members)]

    # create notification
    for m in project_members:
        # print (m.id, m.name)
        un = UploadNotification(
            contact_id = m,
            category='gap',
            project_id = project_id
        )
        un.save()

    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, email_list)
    #print(email_subject)
    #print(email_body)
