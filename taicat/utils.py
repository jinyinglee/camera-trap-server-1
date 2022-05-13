import csv
from tempfile import NamedTemporaryFile
import collections

from operator import itemgetter
from datetime import (
    datetime,
    date
)
import logging
from calendar import (
    monthrange,
    monthcalendar
)

from django.core.cache import cache
from django.db.models import (
    Max,
    Min,
    Count
)
from django.db.models.functions import (
    Trunc,
    ExtractDay,
)
from django.db import connection
from django.utils import timezone
from django.utils.timezone import make_aware

from openpyxl import Workbook
import requests

from taicat.models import (
    Project,
    Image,
    StudyArea,
    Deployment,
    DeploymentJournal,
    DeploymentStat,
    ProjectMember,
    Contact,
    Organization,
    Species,
    ProjectSpecies,
    ProjectStat,
    HomePageStat,
    DeletedImage,
)




# WIP
def display_working_day_in_calendar_html(year, month, working_day):
    month_cal = monthcalendar(year, month)
    s = '| 一 | 二 | 三 | 四 | 五 | 六 | 日 |'
    
    for week in month_cal:
        for d in week:
            s += f'{d}'
    '''
    print (month_cal)
    s = '<table class="table"><tr><th>一</th><th>二</th><th>三</th><th>四</th><th>五</th><th>六</th><th>日</th></tr>'
    for week in month_cal:
        s += '<tr>'
        for d in week:
            #if d > 0:
            #    if working_day[d-1]:
            #        pass
                    #s
            #else:
            #    pass
            #    #res_week.append('0')
            s += '<td>{}</td>'.format(d)
        s += '</tr>'
    s += '</table>'
    '''
    return s

def find_deployment_working_day(year, month, dep_id=''):
    num_month = monthrange(year, month)[1]
    month_start = make_aware(datetime(year, month, 1))
    month_end = make_aware(datetime(year, month, num_month))
    month_stat = [0] * num_month

    query = DeploymentJournal.objects.filter(
        is_effective=True,
        deployment_id=dep_id,
        working_start__lte=month_end,
        working_end__gte=month_start).order_by('working_start')

    ret = []
    for i in query.all():
        # updated
        #print ('-------')
        #print (i.working_start.toordinal(), i.working_end.toordinal(), dt1.toordinal(), dt2.toordinal())
        month_stat_part = [0] * num_month
        overlap_range = [max(i.working_start, month_start), min(i.working_end, month_end)]
        gap_days = (overlap_range[0]-month_start).days
        duration_days = (overlap_range[1]-overlap_range[0]).days+1
        for index, stat in enumerate(month_stat):
            if index >= gap_days and index < gap_days + duration_days:
                    month_stat[index] = 1
                    month_stat_part[index] = 1
            #print(month_stat_part)
        ret.append([i.working_start.strftime('%Y-%m-%d'), i.working_end.strftime('%Y-%m-%d')])
    #print('fin',dep_id, year, month,  month_stat)
    return month_stat, ret


class Calculation(object):
    query = None
    query_no_species = None
    object_list = []
    calculate_params = {}
    calculate_result = None

    def __init__(self, params, auth_project_ids=[]):

        # apply filter
        self.query, self.query_no_species = self.make_basic_query(params, auth_project_ids)
        #print (self.query.query)
        #print (self.query_no_species.query)
        logging.debug(self.query.query)

        # calculate params
        if t1 := params.get('interval', ''):
            self.calculate_params['interval'] = int(t1[0])
        if t2 := params.get('interval2', ''):
            self.calculate_params['interval2'] = int(t2[0])
        if x := params.get('session', ''):
            self.calculate_params['session'] = x[0]

    def make_basic_query(self, params, auth_project_ids=[]):
        query = Image.objects.filter()
        species = None

        # species
        if sp := params.get('species', ''):
            species = sp[0]

        # time range
        if params.get('date_start', '') and params.get('date_end', ''):
            date_start = datetime.strptime(params['date_start'][0], '%Y-%m-%d')
            date_end = datetime.strptime(params['date_end'][0], '%Y-%m-%d')
            query = query.filter(datetime__range=[date_start, date_end])

        # deployment scope
        dep_id_list = []
        if deps := params.get('deployment', ''):
            dep_id_list = deps
        elif sa := params.get('studyarea', ''):
            query = query.filter(studyarea_id=sa[0])
            sa_obj = StudyArea.objects.get(pk=sa[0])
            if sa_obj:
                dep_id_list = [x.id for x in sa_obj.deployment_set.all()]
        if len(dep_id_list):
            # TODO need check project auth
            query = query.filter(deployment_id__in=dep_id_list)


        # check auth project
        project_ids = []
        ## 選 keyword 就不管計劃
        if keyword_list := params.get('keyword'):
            keyword = keyword_list[0]
            proj_list = Project.objects.values_list('id', flat=True).filter(keyword__contains=keyword).all()
            project_ids = list(set(auth_project_ids).intersection(set(proj_list)))
        elif proj_list := params.get('project'):
            project_ids = [int(x) for x in proj_list if int(x) in auth_project_ids]

        if len(project_ids) == 0:
            project_ids = auth_project_ids

        query = query.filter(project_id__in=project_ids)

        query_no_species = query
        if species:
            query = query.filter(annotation__contains=[{'species': species}])

        return query, query_no_species

    def group_by_deployment(self, query):
        return query.values('deployment', 'deployment__name').annotate(count=Count('deployment')).order_by()

    def count_working_hour(self, query):
        '''相機工作時數
        為每台相機實際工作的時數。由使用者於行程管理中所設定的相機有效開始工作時間及結束時間的範圍相減，計算至小時。
        '''
        agg = query.aggregate(Max('datetime'), Min('datetime'))
        if agg['datetime__max'] and agg['datetime__min']:
            #diff_days = (agg['datetime__max'] - agg['datetime__min']).day + 1
            diff_days = (agg['datetime__max']-agg['datetime__min']).days + 1
            working_hour = diff_days * 24 # 當天有照片就算工作 1 天 (24 hr)
            #print (working_hour, agg)

            return [working_hour, [agg['datetime__min'], agg['datetime__max']]]
        return [0, ]

    def count_image(self, query, minutes):
        '''有效照片數
        在自訂的「時間判定間隔」內，無法辨識個體的同物種照片，視為一有效照片，也就是 (總照片數)–(連拍同一隻動物的照片數) = 有效照片數。
        '''
        last_datetime = None
        count = 0
        for image in query.all():
            if last_datetime:
                delta = image['datetime'] - last_datetime
                if ((delta.days * 86400) + (delta.seconds / 3600)) > minutes * 60:
                    count += 1
            else:
                # 第一張有效照片, 直接加 1
                count += 1

            last_datetime = image['datetime']

        return count

    def count_event(self, query, minutes, working_hour):
        '''目擊事件
        此指標計算每台相機捕獲到動物的總事件數（e），並除以該相機之總工作時數（L）做標準化，亦即e / L。事件數定義為：前後相鄰兩張同種之動物照片若間隔 m 分鐘內視為同一事件，不考慮同一張照片內之個體數，亦不辨識個體。其中 m 可從「時間判定間隔」選擇。
        '''
        last_datetime = None
        count = 0
        for image in query.order_by('datetime'):
            delta = image['datetime'] - last_datetime if last_datetime else 0
            if delta:
                if ((delta.days * 86400) + (delta.seconds / 3600)) > minutes * 60:
                    count += 1
            last_datetime = image['datetime']

        if working_hour > 0:
            event_num = count * 1.0 / working_hour
            return (count, (event_num, working_hour))
        else:
            return 0, 0

    def find_next_month(self, year, month):
        month2 = month + 1
        year2 = year
        if month2 > 12:
            month2 = 1
            year2 += 1
        return (year2, month2)

    def count_pod(self,  working_day, year='', month=''):
        '''捕獲回合比例 proportion of occasions with detections
此項指標將每台相機於每回合（可選擇資料之時間範圍全部 或 依每月計算）中的拍攝視為一個試驗（trial），每次的試驗區分為成功（拍攝到動物，不計個體數或頻率）或不成功（未拍攝到動物）兩種結果，並計算每回合每台相機的成功機率（成功次數/試驗次數，亦即相機捕獲動物之回合數/當期回合數），再計算所有相機的平均成功機率。
        '''
        #if working_hour[0] == 0:
        #    return (0,)

        if year and month:
            #ym2 = self.find_next_month(year, month)
            #next_first_day = date(ym2[0], ym2[1], 1)
            #this_first_day = date(year, month, 1)
            #days_in_month = (next_first_day - this_first_day).days
            #days_no_image = 0
            #days_no_image += (working_hour[1][0].date() - this_first_day).days
            #days_no_image += (next_first_day - working_hour[1][1].date()).days
            ##print(year, month, days_in_month, working_hour[1], x, y)
            days_in_month = len(working_day)
            days_no_image = days_in_month - sum(working_day)
            return (days_no_image / days_in_month, (days_no_image, days_in_month))

        else:
            return (0, )

    def count_apoa(self, year, month, query):
        '''活動機率, apparent probability of activity, APOA
        動物在每小時當中被拍攝到的機率。此指標定義為「累計所有相機在每個小時的d 值（detection, 同上），並除以每個小時的取樣次數」。依此定義，每個小時的APOA最小值為0，最大值為1。'''
        ym2 = self.find_next_month(year, month)
        next_first_day = date(ym2[0], ym2[1], 1)
        this_first_day = date(year, month, 1)
        days_in_month = (next_first_day - this_first_day).days
        res = {}
        for i in range(1, days_in_month+1):
            res[i] = [[0, 0]] * 24
            d_in_day = 0
            #print (year, month, i, date(year, month, i))
            group_by_hour = query.filter(datetime__day=i).annotate(hour=Trunc('datetime', 'hour')).values('hour').annotate(hour_count=Count('*')).order_by('hour')
            for x in group_by_hour:
                res[i][x['hour'].hour] = [1, x['hour_count']]
        return res

    def calculate(self):
        deployment_set = self.group_by_deployment(self.query_no_species)
        result = {
            'deployment': {},
            'year_list': [],
            'month_list': [],
        }
        year_range = [0, 0]
        month_range = [0, 0]
        self.query = self.query.values('datetime')
        self.query_no_species = self.query_no_species.values('datetime')

        sess = self.calculate_params.get('session', '')

        for dep in deployment_set:
            #print('#', dep['deployment'], dep['deployment__name'], dep['count'], dep)
            sess_list = []
            if sess == 'all':
                session_query = self.query_no_species.filter(deployment_id=dep['deployment'])
                session_query2 = self.query.filter(deployment_id=dep['deployment'])
                working_hour = self.count_working_hour(session_query)
                image_num = self.count_image(session_query2, self.calculate_params.get('interval'))
                oi3 = (image_num * 1.0 / working_hour[0]) * 1000 if image_num > 0 else 0
                event_num = self.count_event(session_query2, self.calculate_params.get('interval2'), working_hour[0])
                #pod = self.count_pod(working_hour)

                sess_list.append({
                    'working_hour': working_hour,
                    'image_num': image_num,
                    'oi3': oi3,
                    'event_num': event_num,
                    'pod': 0, #TODO
                    'presence_absence': 0,
                })
            elif sess == 'month':
                dep_group_count = self.query_no_species.filter(deployment_id=dep['deployment']).annotate(month=Trunc('datetime', 'month')).values('month').annotate(month_count=Count('*')).order_by('month')
                for res_deployment_month in dep_group_count:
                    year = res_deployment_month['month'].year
                    month = res_deployment_month['month'].month
                    if year_range[0] == 0 or year < year_range[0]:
                        year_range[0] = year
                    if year > year_range[1]:
                        year_range[1] = year
                    if month_range[0] == 0 or month < month_range[0]:
                        month_range[0] = month
                    if month > month_range[1]:
                        month_range[1] = month

                    session_query = self.query_no_species.filter(deployment_id=dep['deployment'], datetime__year=year, datetime__month=month)
                    session_query2 = self.query.filter(deployment_id=dep['deployment'], datetime__year=year, datetime__month=month)
                    ret = find_deployment_working_day(year, month, dep['deployment'])
                    working_day = ret[0]
                    working_hour = sum(working_day) * 24
                    working_hour_old = self.count_working_hour(session_query)
                    #print (working_hour2, working_hour)
                    image_num = self.count_image(session_query2, self.calculate_params.get('interval'))
                    oi3 = (image_num * 1.0 / working_hour) * 1000 if image_num > 0 and working_hour > 0 else 0
                    event_num = self.count_event(session_query2, self.calculate_params.get('interval2'), working_hour)
                    pod = self.count_pod(working_day, year, month)
                    #apoa = self.count_apoa(year, month, session_query)
                    #print(len(apoa))
                    sess_list.append({
                        'year': year,
                        'month': month,
                        #'count': res_deployment_month['month_count'],
                        'working_hour': working_hour,
                        'image_num': image_num,
                        'oi3': oi3,
                        'event_num': event_num,
                        'pod': pod,
                        'presence_absence': 1 if pod[0] else 0,
                        #'apoa': apoa,
                    })

            result['deployment'][dep['deployment']] = {
                'count': dep['count'],
                'name': dep['deployment__name'],
                'session_list': sess_list,
            }
        result.update({
            'year_list': list(range(year_range[0], year_range[1]+1)),
            'month_list': list(range(month_range[0], month_range[1]+1)),
            'session': sess,
        })

        self.calculate_result = result
        return result


def get_species_list(force_update=False):
    CACHE_KEY = 'species_list'
    species_list = cache.get(CACHE_KEY)
    if not force_update and species_list:
        return species_list
    else:
        species_list = count_all_species_list()
        #print('save', species_list)
        cache.set(CACHE_KEY, species_list, 86400) # 1d
        return species_list

def count_all_species_list():
    all_species_list = []
    ret = {}
    for p in Project.objects.all():
        img_list = Image.objects.values_list('annotation', flat=True).filter(project_id=p).all()
        project_species_list = []
        for alist in img_list:
            for a in alist:
                try:
                    if sp := a.get('species', ''):
                        project_species_list.append(sp)
                        all_species_list.append(sp)
                except:
                    #print ('annotation load error')
                    pass
        counter = collections.Counter(project_species_list)
        counter_dict = dict(counter)
        project_species_list = sorted(counter_dict.items(), key=itemgetter(1), reverse=True)
        #print(p, p.id, project_species_list, len(img_list))
        ret[p.id] = project_species_list
    counter_all = collections.Counter(all_species_list)
    counter_dict_all = dict(counter_all)
    all_species_list = sorted(counter_dict_all.items(), key=itemgetter(1), reverse=True)
    ret['all'] = all_species_list

    return ret


def calc_by_species_deployments(species, deployment_id, query, calc_data, results):
    '''
    species: <str> species name: 山羌
    deployment_id: <int>
    query: <QuerySet>
    calc_data: <json> calculation filter
    results: <dict> calculated data
    '''
    query = query.values('datetime')
    image_interval = int(calc_data['imageInterval'])
    event_interval = int(calc_data['eventInterval'])
    # count each deployment
    for i in DeploymentStat.objects.filter(deployment_id=deployment_id, session='month'):
        # find working hour
        if i.year and str(i.year) in results[species] and i.month and i.count_working_hour:
            results[species][str(i.year)][i.month-1]['working_hour'] = i.count_working_hour

            # count image num
            query_image = query.filter(
                deployment_id=deployment_id,
                datetime__year=i.year,
                datetime__month=i.month,
                species=species
            )

            last_datetime = None
            image_count = 0
            for image in query_image.all():
                if last_datetime:
                    delta = image['datetime'] - last_datetime
                    if ((delta.days * 86400) + (delta.seconds / 3600)) > image_interval * 60:
                        image_count += 1
                else:
                    # 第一張有效照片, 直接加 1
                    image_count += 1

                last_datetime = image['datetime']

            oi3 = (image_count * 1.0 / i.count_working_hour) * 1000
            results[species][str(i.year)][i.month-1]['oi3'] = oi3

            # count event num
            last_datetime = None
            count = 0
            for image in query_image.order_by('datetime').all():
                delta = image['datetime'] - last_datetime if last_datetime else 0
                if delta:
                    if ((delta.days * 86400) + (delta.seconds / 3600)) > event_interval * 60:
                        count += 1
                last_datetime = image['datetime']

            event_num = count * 1.0 / i.count_working_hour
            results[species][str(i.year)][i.month-1]['num_event'] = event_num

            # count pod & presence_absence
            days_in_month = monthrange(i.year, i.month)[1]
            results[species][str(i.year)][i.month-1]['days_in_month'] = days_in_month
            image_group_by_day = query_image.values('datetime__day').annotate(count=Count('datetime__day')).order_by('datetime__day')
            results[species][str(i.year)][i.month-1]['pod'] = image_group_by_day.count() / days_in_month # 用總台天算?
            results[species][str(i.year)][i.month-1]['presence'] = 1 if results[species][str(i.year)][i.month-1]['pod'] > 0 else 0
            # count apoa
            image_group_by_hour = query_image.values('datetime__day', 'datetime__hour').annotate(count=Count('*')).order_by('datetime__day', 'datetime__hour')
            # init apoa fill zero
            results[species][str(i.year)][i.month-1]['apoa'] =  [[0 for hour in range(0, 24)] for day in range(0, 31)]
            #[[0] * 24] * days_in_month => failed
            for day_hour in image_group_by_hour:
                results[species][str(i.year)][i.month-1]['apoa'][day_hour['datetime__day']-1][day_hour['datetime__hour']-1] = day_hour['count']

    return results


def calc(query, calc_data):
    #print('query', calc_data)

    agg = query.aggregate(Max('datetime'), Min('datetime'))

    results = {} # by species/deployment/year/month
    # group by species
    species_list = query.values('species').annotate(count=Count('species')).order_by()
    # group by deployment
    deployment_list = query.values('deployment', 'deployment__name').annotate(count=Count('deployment')).order_by()

    #print(species_list.query, species_list, flush=True)
    #print(deployment_list, agg, query.query,flush=True)
    for species in species_list:
        species_name = species['species']
        results[species_name] = {}
        # default round: month
        for dep in deployment_list:
            # fill month year
            for y in range(agg['datetime__min'].year, agg['datetime__max'].year+1):
                results[species_name][str(y)] = []
                for m in range(1, 13):
                    item = {
                        'year': y,
                        'month': m,
                        'species': species_name,
                        'days_in_month': 0, # 總台天?
                        'deployment': dep['deployment__name'],
                        'working_hour': 0,
                        'num_image': 0,
                        'num_event': 0,
                        'oi3': 0,
                        'pod': 0,
                        'presence': 0,
                        'apoa': None,
                    }
                    results[species_name][str(y)].append(item)

            # do calc by species/deployment
            results = calc_by_species_deployments(
                species_name,
                dep['deployment'],
                query,
                calc_data,
                results)


    #print('----', results, flush=True)
    return results

def calc_output(results, file_format, filter_str, calc_str):
    '''
    filter_str, calc_str for display query condition
    '''
    if file_format == 'csv':
        '''csv 多物種會全部放在一個大表
        '''
        #with tempfile.TemporaryFile('w+t') as fp:
        with NamedTemporaryFile('w+t') as tmp:
            tmp.write('filters:'+ filter_str + 'calc:' + calc_str + '\n')
            tmp.write('==='+'\n')
            tmp.write('year,month,物種,days in month,相機位置,相機工作時數,有效照片數,目擊事件數,OI3,捕獲回合比例,存缺,'+','.join(f'活動機率day{day}' for day in range(1, 32))+'\n')
            for sp in results:
                for y in results[sp]:
                    for m, value in enumerate(results[sp][y]):
                        row = []
                        for x in value:
                            if x != 'apoa':
                                row.append(str(value[x]))
                            else:
                                if value[x] != None:
                                    for day in value[x]:
                                        hours = '|'.join([str(d) for d in day])
                                        row.append(hours)

                        #print (row)
                        tmp.write(','.join(row) + '\n')

            tmp.seek(0)
            return tmp.read()

    elif file_format == 'excel':
        with NamedTemporaryFile() as tmp:
            wb = Workbook()
            ws = wb.active
            query_condition = 'filters:'+ filter_str + 'calc:' + calc_str
            ws.cell(row=1, column=1, value=query_condition)
            sheets = []
            sheet_index = 0
            for sp in results:
                row_index = 1
                sheets.append(wb.create_sheet(title=sp))
                header_str = 'year,month,物種,days in month,相機位置,相機工作時數,有效照片數,目擊事件數,OI3,捕獲回合比例,存缺,'+','.join(f'活動機率day{day}' for day in range(1, 32))
                header_list = header_str.split(',')
                for h, v in enumerate(header_list):
                    sheets[sheet_index].cell(row=1, column=h+1, value=v)

                for y in results[sp]:
                    for m, value in enumerate(results[sp][y]):
                        row_index += 1
                        col_index = 0
                        for x in value:
                            if x != 'apoa':
                                col_index += 1
                                sheets[sheet_index].cell(row=row_index, column=col_index, value=str(value[x]))
                            else:
                                if value[x] != None:
                                    for day in value[x]:
                                        col_index += 1
                                        hours = '|'.join([str(d) for d in day])
                                        sheets[sheet_index].cell(row=row_index, column=col_index, value=hours)



                sheet_index += 1

            wb.save(tmp.name)
            tmp.seek(0)
            return tmp.read()

def get_my_project_list(member_id, project_list=[]):
    # 1. select from project_member table
    with connection.cursor() as cursor:
        query = "SELECT project_id FROM taicat_projectmember where member_id ={}"
        cursor.execute(query.format(member_id))
        temp = cursor.fetchall()
        for i in temp:
            if i[0]:
                project_list += [i[0]]
    # 2. check if the user is organization admin
    if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
    if if_organization_admin:
        organization_id = if_organization_admin.values('organization').first()['organization']
        temp = Organization.objects.filter(id=organization_id).values('projects')
        for i in temp:
            project_list += [i['projects']]
    return project_list


def get_project_member(project_id):
    member_list = []
    members = list(ProjectMember.objects.filter(project_id=project_id).all().values('id'))
    organization_id = Organization.objects.filter(projects=project_id).values('id')
    for i in organization_id:
        members += list(Contact.objects.filter(organization=i['id'], is_organization_admin=True).all().values('id'))
    for m in members:
        if m['id'] not in members:
            member_list += [m['id']]
    return member_list


def set_deployment_journal(data, deployment):
    # if data.get('trip_start') and data.get('trip_end') and data.get('folder_name') and data.get('source_id'):  # 不要判斷了

    dj_exist = DeploymentJournal.objects.filter(
        deployment=deployment,
        folder_name=data['folder_name'],
        local_source_id=data['source_id']).first()

    if dj_exist:
        is_modified = False
        if data.get('trip_start') and data.get('trip_end'):
            if data['trip_start'] != dj_exist.working_start:
                dj_exist.working_start = data['trip_start']
                is_modified = True
            if data['trip_end'] != dj_exist.working_end:
                dj_exist.working_end = data['trip_end']
                is_modified = True

        if is_modified:
            dj_exist.last_updated = timezone.now()
            dj_exist.save()

        deployment_journal_id = dj_exist.id

    else:
        dj_new = DeploymentJournal(
            deployment_id=deployment.id,
            project=deployment.project,
            studyarea=deployment.study_area,
            is_effective=False,
            folder_name=data['folder_name'],
            local_source_id=data['source_id'],
            last_updated=timezone.now()
        )

        if x := data.get('trip_start'):
            dj_new.trip_start = x
        if x := data.get('trip_end'):
            dj_new.trip_end = x

        dj_new.save()

        deployment_journal_id = dj_new.id

    # 有時間才算有效
    if data.get('trip_start') and data.get('trip_end'):
        dj_new.is_effective = True

    return deployment_journal_id

def clone_image(obj):
    new_img = Image(
        deployment=obj.deployment,
        project=obj.project,
        studyarea=obj.studyarea,
        file_url=obj.file_url,
        filename=obj.filename,
        datetime=obj.datetime,
        count=obj.count,
        image_hash=obj.image_hash,
        image_uuid=obj.image_uuid,
        has_storage=obj.has_storage,
        folder_name=obj.folder_name,
        specific_bucket=obj.specific_bucket,
        deployment_journal=obj.deployment_journal
    )
    new_img.save()
    return new_img

def set_image_annotation(image_obj):
    '''extract annotation (json field) to seperate field, ex: species, life_stage...
    '''
    def update_annotation_field(obj, values):
        # (annotation_field, model field)
        field_map = {
            'species': 'species',
            'lifestage': 'life_stage', # 該死的 _
            'sex': 'sex',
            'antler': 'antler',
            'remark': 'remarks', # 該死的 s
            'animal_id': 'animal_id',
        }
        for field in field_map:
            if v := values.get(field):
                setattr(obj, field_map[field], v)
        obj.last_updated = timezone.now()

    if annotation := image_obj.annotation:
        related_images = Image.objects.filter(image_uuid=image_obj.image_uuid).order_by('annotation_seq').all()
        num_related = len(related_images)
        num_annotation = len(annotation)
        # print (num_related, num_annotation, flush=True)
        to_delete = []
        for i in range(0, max(num_annotation, num_related)):
            if i == 0:  # original image
                update_annotation_field(image_obj, annotation[0])
                image_obj.save()
            elif num_related - num_annotation <=0:  # new annotation (cloned image)
                if i < num_related:
                    update_annotation_field(related_images[i], annotation[i])
                    related_images[i].save()
                else:
                    cloned = clone_image(image_obj)
                    update_annotation_field(cloned, annotation[i])
                    cloned.annotation_seq = i
                    cloned.save()
            elif num_related - num_annotation > 0: # delete cloned image
                if i < num_annotation:
                    update_annotation_field(related_images[i], annotation[i])
                    related_images[i].save()
                else:
                    to_delete = [x.id for x in related_images if x.annotation_seq > 0]
                    break

        if len(to_delete) > 0:
            #print(to_delete, flush=True)
            delete_image_by_ids(to_delete, image_obj.project_id)
            # 全部刪掉再重建
            for i, a in enumerate(image_obj.annotation):
                if i > 0:
                    cloned = clone_image(image_obj)
                    update_annotation_field(cloned, annotation[i])
                    cloned.annotation_seq = i
                    cloned.save()


def delete_image_by_ids(image_list=[], pk=None):
    now = timezone.now()
    image_objects = Image.objects.filter(id__in=image_list)
    # species的資料先用id抓回來計算再扣掉
    query = image_objects.values('species').annotate(total=Count('species')).order_by('-total')
    for q in query:
        # taicat_species
        if sp := Species.objects.filter(name=q['species']).first():
            if sp.count == q['total']:
                sp.delete()
            else:
                sp.count -= q['total']
                sp.last_updated = now
                sp.save()
        # taicat_projectspecies
        if p_sp := ProjectSpecies.objects.filter(name=q['species'], project_id=pk).first():
            if p_sp.count == q['total']:
                p_sp.delete()
            else:
                p_sp.count -= q['total']
                p_sp.last_updated = now
                p_sp.save()

    if ProjectStat.objects.filter(project_id=pk).exists():
        p = ProjectStat.objects.get(project_id=pk)
        p.num_data -= image_objects.count()
        p.last_updated = now
        p.save()

    year = image_objects.aggregate(Min('datetime'))['datetime__min'].strftime("%Y")
    home = HomePageStat.objects.filter(year__gte=year)
    for h in home:
        h.count -= image_objects.count()
        h.last_updated = now
        h.save()

    # move deleted image to DeletedImage table
    image_dict = image_objects.values()
    for d in image_dict:
        di = DeletedImage(**d)
        di.save()
    Image.objects.filter(id__in=image_list).delete()

    species = ProjectSpecies.objects.filter(project_id=pk).order_by('count').values('count', 'name')
    return list(species)
