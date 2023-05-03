import pytz
import json
from datetime import datetime
import csv
from pathlib import Path

from bson.objectid import ObjectId

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery import shared_task
from celery.utils.log import get_task_logger

from taicat.utils import (
    save_calculation,
    apply_search_filter,
)

logger = get_task_logger(__name__)

from taicat.models import (
    Image,
    Image_info,
    Deployment,
    DeploymentJournal,
    DownloadLog,
    ParameterCode,
    Contact,
)
from base.models import UploadHistory
from .utils import (
    set_image_annotation,
    calculated_data,
    calc_output,
)

@shared_task
def process_image_annotation_task(deployment_journal_id, data):
    datetime_from = None
    datetime_to = None
    species_list = []

    deployment_journal = DeploymentJournal.objects.get(pk=deployment_journal_id)
    deployment_journal.upload_status = 'start-annotation'
    next_status = 'start-media'
    # aware datetime object
    utc_tz = pytz.timezone(settings.TIME_ZONE)

    # find if is specific_bucket
    bucket_name = data.get('bucket_name', '')
    specific_bucket = ''
    if bucket_name != settings.AWS_S3_BUCKET:
        specific_bucket = bucket_name

    folder_name = data.get('folder_name', '')

    for i in data['image_list']:
        img_info_payload = None
        # prevent json load error
        exif_str = i[9].replace('\\u0000', '') if i[9] else '{}'
        exif = json.loads(exif_str)
        anno = json.loads(i[7]) if i[7] else '{}'
        if image_id := i[11]:
            next_status = 'finished' # re-upload

            try:
                img = Image.objects.get(pk=image_id)
            except Image.DoesNotExist:
                print ('Does Not Exist!')
                continue

            # only update annotation
            img.annotation = anno
            img.source_data.update({'id': i[0]})
            img.last_updated = datetime.now()

        else:
            for a in anno:
                if sp := a.get('species', ''):
                    if sp not in species_list:
                        species_list.append(sp)

            dt_ = datetime.fromtimestamp(i[3], utc_tz)
            if datetime_from is None or dt_ < datetime_from:
                datetime_from = dt_
            elif datetime_to is None or dt_ > datetime_to:
                datetime_to = dt_

            image_uuid = str(ObjectId())
            img = Image(
                deployment_id=deployment_journal.deployment_id,
                source_data={'id': i[0]},
                filename=i[2],
                datetime=dt_,
                image_hash=i[6],
                annotation=anno,
                memo=data['key'],
                image_uuid=image_uuid,
                has_storage='N',
                folder_name=folder_name,
                deployment_journal_id=deployment_journal.id,
            )

            if specific_bucket != '':
                img.specific_bucket = specific_bucket

            img_info_payload = {
                'source_data': i,
                'exif': exif,
                'image_uuid': image_uuid
            }
            if pid := deployment_journal.project_id:
                img.project_id = pid
            if said := deployment_journal.studyarea_id:
                img.studyarea_id = said

            # seperate image_info
            img_info = Image_info(
                image_uuid=img_info_payload['image_uuid'],
                source_data=img_info_payload['source_data'],
                exif=img_info_payload['exif'],
            )
            img_info.save()


        img.save()
        #image_map[i[0]] = [img.id, img.image_uuid]
        set_image_annotation(img)

    # done
    deployment_journal.upload_status = next_status
    deployment_journal.save()

    save_calculation(species_list, datetime_from, datetime_to, deployment_journal.deployment)


@shared_task
def process_download_data_task(email, filter_dict, member_id, host):
    download_dir = Path(settings.MEDIA_ROOT, 'download')
    filename = f'download_{str(ObjectId())}_{datetime.now().strftime("%Y-%m-%d")}.csv'
    query = apply_search_filter(filter_dict)
    header = ['計畫ID', '計畫名稱', '影像ID', '樣區/子樣區', '相機位置', '檔名', '拍攝時間', '物種', '年齡', '性別', '角況', '個體ID', '備註']
    with open(Path(download_dir, filename), 'w') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(header)
        for i in query.all():
            row = [
                i.project_id,
                i.project.name,
                i.image_uuid,
                i.studyarea.name,
                i.deployment.name,
                i.filename,
                i.datetime.strftime('%Y-%m-%d %H:%M:%S') if i.datetime else '',
                i.species,
                i.life_stage,
                i.sex,
                i.antler,
                i.animal_id,
                i.remarks
            ]
            spamwriter.writerow(row)

    download_url = "https://{}{}{}".format(
        host,
        settings.MEDIA_URL,
        Path('download', filename))

    user_role = ''
    if contact := Contact.objects.get(id=member_id):
        if role := ParameterCode.objects.filter(parametername=contact.identity).first():
            user_role = role.name

    # download_lo
        #condiction_log = f'''專案名稱:{project_name}, 日期：{date_filter}。樣區 / 相機位置：{conditions} 。物種：{spe_conditions} 。時間：{time_filter}。縣市：{county_filter}。保護留區：{protectarea_filter}。資料夾：{folder_filter} 。'''
    download_log_sql = DownloadLog(
        user_role=user_role,
        condiction=json.dumps(filter_dict),
        file_link=download_url)
    download_log_sql.save()

    email_subject = '[臺灣自動相機資訊系統] 下載資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])


@shared_task
def process_download_calculated_data_task(email, filter_dict, calc_dict, calc_type, out_format, calc_data, host):
    results = calculated_data(filter_dict, calc_data)
    content = calc_output(results, out_format, json.dumps(filter_dict), json.dumps(calc_data))

    ext = 'csv' if out_format == 'csv' else 'xlsx'
    filename = f'download_calculated_{str(ObjectId())}_{datetime.now().strftime("%Y-%m-%d")}.{ext}'
    download_dir = Path(settings.MEDIA_ROOT, 'download')
    with open(Path(download_dir, filename), 'wb') as outfile:
        outfile.write(content)

    download_url = "https://{}{}{}".format(
        host,
        settings.MEDIA_URL,
        Path('download', filename))
    email_subject = '[臺灣自動相機資訊系統] 下載計算資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    #print('email', email_subject, email_body)
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])
