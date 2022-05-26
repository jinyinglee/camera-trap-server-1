# API

## Upload data 上傳相關

URL: `/update_upload_history`

source: `base\views.update_upload_history`

用POST傳

```
status: finished/uploading
deployment_journal_id:
```

## Search

URL: `/api/search`

Source: `taicat/search_view.py`: api_search

Parameter:

- filter

  - projects
  - species
  - startDate / endDate
  - deployments
  - studyareas

### Calculation

Source: `taicat.utils` calc, calc_output

calc -> calc_by_species_deployments

## Model

### Project

**get_deployment_list**: 取得改計畫下所有相機位置 (按照樣區分層存放)

**count_deployment_journal**: 算某年度下的行程資訊 (月曆) （沒給年份就全算）

**get_or_count_stats**: 抓算好的 project stats，如果沒有，就重新算一次，就是去執行 `count_deployment_journal`

### Deployment 

**count_working_day**: 計算相機工作時數 (根據 DeploymentJournal 記錄)

### 相機行程/管考

**get_species_images(self, year)**: 查某相機位置某年度物種/照片比例，查看 cache 有無資料

- 沒有就呼叫 `count_species_images`
- cache key: `SPIMG_{self.id}_{year}`，保存 100 天
- 用 `count-projectoversight-species-images-cache.py`  產生 cache

**count_species_images(self, year)**: 實際計算某相機位置，某年度物種/照片比例

相關 scripts:

`scripts/count-project-stats.py` 產生計畫的管考需要的資料 (stats)


資料結構:

```
  data -> years -> studyareas -> items -> deployments -> items -> month_list
  data: dict (datetime__range, working__range, updated, elapsed, years)
  years: dict, ex: str(2019)
  studyareas: list (item dict: {name, items, sa_idx})
  deployments: list (item dict: {name, items, d_idx, ratio_year, gaps})
  month_list: list (item list: [year, month, deployment_name, count_working_day, days_in_month, month_calendar, working_day, deployment_journal_range]
```
