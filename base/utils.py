from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.core.cache import cache
import time
from django.db import connection
from taicat.models import Image


class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)


generate_token = TokenGenerator()


def get_cache_growth_data():

    data_growth_image = cache.get('growth_image')
    data_growth_deployment = cache.get('growth_deployment')

    if not data_growth_image:
        print('calculate data_growth_image')
        with connection.cursor() as cursor:
            query = """SELECT EXTRACT (year FROM datetime) as year, count(id) as count
            FROM taicat_image
            GROUP BY year
            """
            cursor.execute(query)
            data_growth_image = cursor.fetchall()
            data_growth_image = pd.DataFrame(data_growth_image, columns=[
                'year', 'num_image']).sort_values('year')
            year_min, year_max = int(data_growth_image.year.min()), int(
                data_growth_image.year.max())
            year_gap = pd.DataFrame(
                [i for i in range(2008, year_max)], columns=['year'])
            data_growth_image = year_gap.merge(
                data_growth_image, how='left').fillna(0)
            data_growth_image['cumsum'] = data_growth_image.num_image.cumsum()
            data_growth_image = data_growth_image.drop(columns=['num_image'])
            data_growth_image = list(
                data_growth_image.itertuples(index=False, name=None))

    if not data_growth_deployment:
        print('calculate data_growth_deployment')
        with connection.cursor() as cursor:
            query = """
                    SELECT MIN(EXTRACT (year FROM datetime)) as year, deployment_id FROM taicat_image
                    GROUP BY deployment_id
            """
            cursor.execute(query)
            data_growth_deployment = cursor.fetchall()
            data_growth_deployment = pd.DataFrame(data_growth_deployment, columns=[
                'year', 'deployment_id']).sort_values('year')
            data_growth_deployment = data_growth_deployment.groupby(
                ['year'], as_index=False).count()
            data_growth_deployment = year_gap.merge(
                data_growth_deployment, how='left').fillna(0)
            data_growth_deployment['cumsum'] = data_growth_deployment.deployment_id.cumsum(
            )
            data_growth_deployment = data_growth_deployment.drop(
                columns=['deployment_id'])
            data_growth_deployment = list(
                data_growth_deployment.itertuples(index=False, name=None))

    response = {'data_growth_image': data_growth_image,
                'data_growth_deployment': data_growth_deployment}

    return response


species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']


def get_cache_species_data():
    species_data = cache.get('species_data')

    if not species_data:
        print('calculate species_data')
        for i in species_list:
            spe_c = Image.objects.filter(
                annotation__contains=[{'species': i}]).count()
            if spe_c > 0:
                species_data += [(spe_c, i)]
        species_data.sort(reverse=True)
        response = {'species_data': species_data}
    return response
