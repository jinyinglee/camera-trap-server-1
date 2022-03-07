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
        <Grid item xs={3}>
          <FormControl fullWidth>
            <InputLabel id="label-round">回合</InputLabel>
            <Select
              labelId="label-round"
              value={calcData.round}
              label="回合"
              onChange={(e)=>setCalcData({...calcData, round: e.target.value})}
            >
              <MenuItem value="month">月</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={3}>
          <FormControl fullWidth>
            <InputLabel id="label-foto-interval">有效照片間隔</InputLabel>
            <Select
              labelId="label-foto-interval"
              value={calcData.fotoInterval}
              label="有效照片間隔"
              onChange={(e)=>setCalcData({...calcData, fotoInterval: e.target.value})}
            >
              <MenuItem value="2">2 分鐘</MenuItem>
              <MenuItem value="5">5 分鐘</MenuItem>
              <MenuItem value="10">10 分鐘</MenuItem>
              <MenuItem value="30">30 分鐘</MenuItem>
              <MenuItem value="60">60 分鐘</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={3}>
          <FormControl fullWidth>
            <InputLabel id="label-event-interval">目擊事件間隔</InputLabel>
            <Select
              labelId="label-event-interval"
              value={calcData.eventInterval}
              label="目擊事件間隔"
              onChange={(e)=>setCalcData({...calcData, eventInterval: e.target.value})}

            >
              <MenuItem value="2">2 分鐘</MenuItem>
              <MenuItem value="5">5 分鐘</MenuItem>
              <MenuItem value="10">10 分鐘</MenuItem>
              <MenuItem value="30">30 分鐘</MenuItem>
              <MenuItem value="60">60 分鐘</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </>
  );
}

export {AppSearchCalculation};
