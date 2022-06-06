import React from 'react';

import Box from '@mui/material/Box';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import Grid from '@mui/material/Grid';

const AppSearchCalculation = ({calcData, setCalcData}) => {
  return (
    <>
      <h3 style={{ marginTop: '50px'}}>分析與計算</h3>
      <Grid container spacing={2}>
        <Grid item xs={2}>
          <FormControl fullWidth>
            <InputLabel id="label-session">回合</InputLabel>
            <Select
              labelId="label-session"
              value={calcData.session}
              label="回合"
              onChange={(e)=>setCalcData({type: 'setCalcData', name: 'session', value: e.target.value})}
            >
              <MenuItem value="month">月</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl required fullWidth>
            <InputLabel id="label-image-interval">有效照片間隔</InputLabel>
            <Select
              labelId="label-image-interval"
              value={calcData.imageInterval}
              label="有效照片間隔"
              onChange={(e)=>setCalcData({type: 'setCalcData', name:'imageInterval', value: e.target.value})}
            >
              <MenuItem value="30">30 分鐘</MenuItem>
              <MenuItem value="60">60 分鐘</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl required fullWidth>
            <InputLabel id="label-event-interval">目擊事件間隔</InputLabel>
            <Select
              labelId="label-event-interval"
              value={calcData.eventInterval}
              label="目擊事件間隔"
              onChange={(e)=>setCalcData({type: 'setCalcData',name:'eventInterval', value: e.target.value})}
            >
              <MenuItem value="2">2 分鐘</MenuItem>
              <MenuItem value="5">5 分鐘</MenuItem>
              <MenuItem value="10">10 分鐘</MenuItem>
              <MenuItem value="30">30 分鐘</MenuItem>
              <MenuItem value="60">60 分鐘</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={4}>
          <FormControl fullWidth>
            <InputLabel id="label-calc-type">計算項目</InputLabel>
            <Select
              labelId="label-calc-type"
              value={calcData.calcType}
              label="計算項目"
              onChange={(e)=>setCalcData({type: 'setCalcData', name:'calcType', value: e.target.value})}
            >
              <MenuItem value="basic-oi">基本（相機工作時數, 有效照片數, 目擊事件數, OI）</MenuItem>
              <MenuItem value="pod">捕獲回合比例、存缺</MenuItem>
              <MenuItem value="apoa">活動機率(APOA)</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={2}>
          <FormControl fullWidth>
            <InputLabel id="label-file-format">檔案格式</InputLabel>
            <Select
              labelId="label-file-format"
              value={calcData.fileFormat}
              label="檔案格式"
              onChange={(e)=>setCalcData({type: 'setCalcData', name:'fileFormat', value:e.target.value})}
            >
              {/*<MenuItem value="csv">csv</MenuItem>*/}
              <MenuItem value="excel">Excel (xlsx)</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </>
  );
}

export {AppSearchCalculation};
