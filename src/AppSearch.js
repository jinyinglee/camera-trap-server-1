import React, {useEffect, useState} from 'react';

import Chip from '@mui/material/Chip';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import DatePicker from '@mui/lab/DatePicker';
import DateAdapter from '@mui/lab/AdapterDateFns';
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import LocalizationProvider from '@mui/lab/LocalizationProvider';
import { zhTW } from 'date-fns/locale';

import { AppSearchDataGrid } from './AppSearchDataGrid';
import { AppSearchCalculation } from './AppSearchCalculation';
import { cleanFormData } from './Utils';

const apiPrefix = 'http://127.0.0.1:8000/api/';


const AppSearch = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [pagination, setPagination] = React.useState({
    page: 0,
    perPage: 10
  });
  const [formData, setFormData] = useState({
    species: [],
    startDate: null,
    endDate: null,
    projects: [],
    keywoard: '',
  });
  const [options, setOptions] = useState({
    species: [],
    projects: [],
  });
  const [result, setResult] = useState(null);
  const [calcData, setCalcData] = React.useState({
    round: 'month',
    fotoInterval: '',
    eventInterval: '',
  });

  useEffect(() => {
    fetch(`${apiPrefix}species`)
    .then(resp => resp.json())
    .then(data => {
      fetch(`${apiPrefix}projects`)
        .then(resp2 => resp2.json())
        .then(data2 => {
          setOptions({
            ...options,
            species: data.data,
            projects: data2.data
          });
        });
    });
  }, []);

  useEffect(() => {
    if (pagination.page !== 0 || pagination.perPage !== 10) {
      // prevent first time fetch (not press submit button yet!)
      fetchData();
    }
  }, [pagination]);

  const fetchData = () => {
    const formDataCleaned = cleanFormData(formData);
    console.log('cleaned', formDataCleaned);
    //const csrftoken = getCookie('csrftoken');
    const d = JSON.stringify(formDataCleaned);
    let searchApiUrl = `${apiPrefix}search?filter=${d}`;

    const pagination2 = (pagination.perPage === 10) ? {page: 0, perPage: 20} : pagination;
    const p = JSON.stringify(pagination2);
    searchApiUrl = `${searchApiUrl}&pagination=${p}`;

    setIsLoading(true);
    console.log('fetch:', searchApiUrl);
    fetch(encodeURI(searchApiUrl), {
      //body: JSON.stringify({filter: formData}),
      mode: 'same-origin',
      headers: {
        'content-type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // for Django request.is_ajax()
        //'X-CSRFToken': csrftoken,
      },
      method: 'GET',
    })
      .then(resp => resp.json())
      .then(data => {
        //console.log(data)
        setResult(data);
        setIsLoading(false);
      });
  };

  const handleSubmit = () => {
    fetchData();
  }

  const handleChangePage = (e, page) => {
    const pp = (pagination.perPage === 10) ? 20 : pagination.perPage;
    setPagination({page: page, perPage: pp});
  }

  const handleChangeRowsPerPage = (e) => {
    setPagination({page: 0, perPage: parseInt(e.target.value, 10)});
  }

  const handleCalc = () => {
    console.log(formData, calcData);
  }
  console.log('formData: ', formData, result);


  return (
    <>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={isLoading}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <h3>篩選條件</h3>
      <LocalizationProvider dateAdapter={DateAdapter} locale={zhTW}>
      <Grid container spacing={2}>
        <Grid item xs={3}>
          <Autocomplete
            multiple
            filterSelectedOptions
            options={options.species}
            getOptionLabel={(option) => option.name}
            value={formData.species}
            onChange={(e, value) => setFormData({...formData, species: value})}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="standard"
                label="物種"
              />
            )}
          />
        </Grid>
        <Grid item xs={3}>
          <DatePicker
            disableFuture
            label="資料啟始日期"
            openTo="year"
            clearable={true}
            views={['year', 'month', 'day']}
            value={formData.startDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => setFormData({...formData, startDate: v})}
            renderInput={(params) => <TextField {...params} variant="standard"/>}
          />
        </Grid>
        <Grid item xs={3}>
          <DatePicker
            disableFuture
            label="資料結束日期"
            clearable={true}
            openTo="year"
            views={['year', 'month', 'day']}
            value={formData.endDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => setFormData({...formData, endDate: v})}
            renderInput={(params) => <TextField {...params} variant="standard" />}
          />
        </Grid>
        <Grid item xs={9}>
          <Autocomplete
            multiple
            options={options.projects}
            getOptionLabel={(option) => option.name}
            value={formData.projects}
            groupBy={(option)=> option.group_by}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="standard"
                label="計畫"
              />
            )}
            onChange={(e, v) => setFormData({...formData, projects: v})}
          />
        </Grid>
        <Grid item xs={3}>
          <TextField
            label="計畫關鍵字"
            variant="standard"
            value={formData.keyword}
            onChange={(e)=> setFormData({...formData, keywoard: e.target.value})}
          />
        </Grid>
        <Grid item xs={3}>
          <Button variant="contained" onClick={handleSubmit}>搜尋</Button>
        </Grid>
        <Grid item xs={12}>
          {(result && result.data.length > 0) ?
           <>
           <AppSearchDataGrid result={result} handleChangePage={handleChangePage} handleChangeRowsPerPage={handleChangeRowsPerPage} pagination={pagination}/>
             <AppSearchCalculation calcData={calcData} setCalcData={setCalcData} />
           <Button variant="contained" onClick={handleCalc} style={{marginTop: '10px'}}>下載計算</Button>
             <div>
           <button type="button" className="btn btn-warning" data-bs-toggle="modal" data-bs-target="#exampleModal" style={{marginTop: '24px'}}>
                 計算項目的說明
               </button>
             </div>
           </>
           : null}
        </Grid>

      </Grid>
      </LocalizationProvider>
    </>
  );
}

export {AppSearch};
