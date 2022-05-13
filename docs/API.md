# API

## Upload data 上傳相關

URL: `/update_upload_history`

source: `base\views.update_upload_history`

用POST傳

```
status: finished/uploading
deployment_journal_id:
```

## Model

### Project

**get_deployment_list**: 取得改計畫下所有相機位置 (按照樣區分層存放)
**count_deployment_journal**: 算某年度下的行程資訊 (月曆) （沒給年份就全算）

### Deployment

**count_working_day**: 計算相機工作時數 (根據 DeploymentJournal 記錄)
**get_species_images(self, year)**: 查某相機位置某年度物種/照片比例，查看 cache 有無資料

- 沒有就呼叫 `count_species_images`
- cache key: `SPIMG_{self.id}_{year}`，保存 100 天
- 用 `count-projectoversight-species-images-cache.py`  產生 cache

**count_species_images(self, year)**: 實際計算某相機位置，某年度物種/照片比例
