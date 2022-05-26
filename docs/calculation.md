# Calculation

## Policy & Rules

### 相機有效工作

用行程來判定，這段時間都算相機正常工作
理想上，相機每天會拍測試照，有測試照的就算當天有工作，但實際上不是每台相機都有設定。


## API


### Cache

有效照片間隔: 30, 60

目擊事件間隔: 2, 5, 10, 30, 60

```
key = f'{dep.id}/{year}/{month}/{species_name}/{img_int}/{e_int}'
```

Models: Deployment.calculate(year, month, species, image_interval, event_interval)
```
[working_days, image_count, event_count, None, None, oi3, pod, mdh]
```
