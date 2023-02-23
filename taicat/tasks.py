import pytz
import json
from datetime import datetime
from bson.objectid import ObjectId

from django.conf import settings

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

from taicat.models import (
    Image,
    Image_info,
    Deployment,
    DeploymentJournal,
)
from base.models import UploadHistory
from .utils import (
    set_image_annotation,
)

@shared_task
def process_image_annotation_task(deployment_journal_id, data):
    deployment_journal = DeploymentJournal.objects.get(pk=deployment_journal_id)
    deployment_journal.upload_status = 'start-annotation'
    # aware datetime object
    utc_tz = pytz.timezone(settings.TIME_ZONE)

    # find if is specific_bucket
    bucket_name = data.get('bucket_name', '')
    specific_bucket = ''
    if bucket_name != settings.AWS_S3_BUCKET:
        specific_bucket = bucket_name

    folder_name = data.get('folder_name', '')

    for i in data['image_list']:
        # logger.info(i)
        img_info_payload = None
        # prevent json load error
        exif_str = i[9].replace('\\u0000', '') if i[9] else '{}'
        exif = json.loads(exif_str)
        anno = json.loads(i[7]) if i[7] else '{}'
        if i[11]:
            img = Image.objects.get(pk=i[11])
            # only update annotation
            img.annotation = anno
            img.source_data.update({'id': i[0]})
            img.last_updated = datetime.now()
        else:
            image_uuid = str(ObjectId())
            img = Image(
                deployment_id=deployment_journal.deployment_id,
                source_data={'id': i[0]},
                filename=i[2],
                datetime=datetime.fromtimestamp(i[3], utc_tz),
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
    deployment_journal.upload_status = 'start-media'
    deployment_journal.save()
