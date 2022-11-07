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
    proj = Project.objects.get(pk=i[0])
    data = proj.count_deployment_journal([i[1]])

    body = '資料缺失: 尚未填寫列表\n----------------------'
    for sa in data[str(i[1])]:
        #body += '\n\n================\n{}\n================\n'.format(sa['name'])
        body += '\n\n# 樣區名稱: {}\n'.format(sa['name'])
        for dep in sa['items']:
            body += '\n## 相機位置: {}\n'.format(dep['name'])
            for gap in dep['gaps']:
                body += '* {}/{}\n'.format(datetime.datetime.fromtimestamp(gap['range'][0]).strftime('%Y-%m-%d'), datetime.datetime.fromtimestamp(gap['range'][1]).strftime('%Y-%m-%d'))

    email_subject = '[臺灣自動相機資訊系統] | {} | 資料缺失: 尚未填寫列表'.format(proj.name)
    email_body= body

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

    #print(email_subject)
    #print(email_body)
