import React, {useEffect, useState} from 'react';

import Chip from '@mui/material/Chip';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import DatePicker from '@mui/lab/DatePicker';
import DateAdapter from '@mui/lab/AdapterDateFns';
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import LocalizationProvider from '@mui/lab/LocalizationProvider';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline';

import { zhTW } from 'date-fns/locale';

import { AppSearchDataGrid } from './AppSearchDataGrid';
import { AppSearchCalculation } from './AppSearchCalculation';
import { cleanFormData } from './Utils';



const AppSearch = () => {
  const today = new Date();
  const todayYMD = `${today.getFullYear()}-${today.getMonth().toString().padStart(2, '0')}-${today.getDay().toString().padStart(2, '0')}`;
  console.log(todayYMD);
  const apiPrefix = process.env.API_PREFIX;
  const [isLoading, setIsLoading] = React.useState(false);
  const [pagination, setPagination] = React.useState({
    page: 0,
    perPage: 10
  });
  const [options, setOptions] = useState({
    species: [],
    projects: [],
    deployments: null,
  });

  const [formData, setFormData] = useState({
    species: [],
    startDate: null,
    endDate: null,
    projects: [],
    projectFilters: [{project: null}],
    keyword: '',
  });
  const [result, setResult] = useState(null);
  const [calcData, setCalcData] = React.useState({
    session: 'month',
    imageInterval: '60',
    eventInterval: '60',
    fileFormat: 'excel',
    calcType: 'basic',
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
        console.log('resp', data)
        setResult(data);
        setIsLoading(false);
      });
  };

  const fetchDeploymentList = (projectId) => {
    let studyareaApiUrl = `${apiPrefix}deployments?project_id=${projectId}`;

    setIsLoading(true);
    fetch(encodeURI(studyareaApiUrl), {
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
        //console.log('resp sa', data)
        let newDeployments = options.deployments || {};
        newDeployments[projectId] = data.data;
        setOptions({...options, deployments: newDeployments})
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
    const formDataCleaned = cleanFormData(formData);
    const calc = JSON.stringify(calcData);
    const d = JSON.stringify(formDataCleaned);
    const searchApiUrl = `${apiPrefix}search?filter=${d}&calc=${calc}&download=1`;
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
      .then(resp => resp.blob())
      .then(blob => {
        const ext_name = (calcData.fileFormat === 'csv') ? 'csv' : 'xlsx';
        // code via: https://stackoverflow.com/a/65609170/644070
        const href = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = href;
        link.setAttribute('download', `camera-trap-calculation-${calcData.calcType}.${ext_name}`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setIsLoading(false);
      });
  }

  const ProjectFilterBox = ({index}) => {
    const projectId = (formData.projectFilters[index].project) ? formData.projectFilters[index].project.id : null;
    const studyareas = formData.projectFilters[index].studyareas || [];
    let deploymentOptions = [];
    for (let i in studyareas) {
      const values = studyareas[i].deployments.map(x=> {x.groupBy = studyareas[i].name; return x});
      deploymentOptions = deploymentOptions.concat(values);
    }
    return (
      <Box sx={{ mt: 1}}>
        <Paper elevation={2} sx={{ p: 3}}>
          <Typography variant="subtitle1">計畫篩選 ({index+1})</Typography>
          <Grid container spacing={2}>
            <Grid item xs={10}>
              <Autocomplete
                options={options.projects}
                getOptionLabel={(option) => option.name}
                value={formData.projectFilters[index].project || null}
                groupBy={(option)=> option.group_by}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="standard"
                    label="計畫名稱"
                  />
                )}
                onChange={(e, v) => {
                  if (v && v.id) {
                    const newArr = [...formData.projectFilters];
                    newArr[index].project = v;
                    setFormData({...formData, projectFilters: newArr});
                    fetchDeploymentList(v.id);
                  }
                }}
                filterOptions={(options, {inputValue}) => {
                  const projectIds = formData.projectFilters.filter(x=>x.project).map(x=>x.project.id);
                  return options.filter(option => (projectIds.indexOf(option.id)<0) && (option.name.indexOf(inputValue) >=0));
                }}
              />
            </Grid>
            <Grid item xs={2} align="right">
              <Button startIcon={<RemoveCircleOutlineIcon/>} onClick={(e)=> {
                const newArr = [...formData.projectFilters];
                newArr.splice(index, 1);
                setFormData({...formData, projectFilters: newArr});
              }}>
                移除
              </Button>
            </Grid>
            {(formData.projectFilters[index].project && options.deployments && options.deployments[projectId]) ?
             <Grid item xs={6}>
               <Autocomplete
                 multiple
                 options={options.deployments[projectId]}
                 getOptionLabel={(option) => option.name}
                 value={formData.projectFilters[index].studyareas || []}
                 renderInput={(params) => (
                   <TextField
                     {...params}
                     variant="standard"
                     label="樣區"
                   />
                 )}
                 onChange={(e, v) => {
                   const newArr = [...formData.projectFilters];
                   newArr[index].studyareas = v;
                   setFormData({...formData, projectFilters: newArr})
                 }}
               />
             </Grid>
             : null}
            {(formData.projectFilters[index].project && options.deployments && formData.projectFilters[index].studyareas && formData.projectFilters[index].studyareas) ?
             <Grid item xs={6}>
               <Autocomplete
                 multiple
                 options={deploymentOptions}
                 getOptionLabel={(option) => `${option.groupBy}: ${option.name}`}
                 value={formData.projectFilters[index].deployments || []}
                 groupBy={(option)=> option.groupBy}
                 renderInput={(params) => (
                   <TextField
                     {...params}
                     variant="standard"
                     label="相機位置"
                   />
                 )}
                 onChange={(e, v) => {
                   const newArr = [...formData.projectFilters];
                   newArr[index].deployments = v;
                   setFormData({...formData, projectFilters: newArr})
                 }}
               />
             </Grid>
             : null}
          </Grid>
        </Paper>
      </Box>
    );
  }

  console.log('render ', formData, result, options, calcData);


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
        <Grid item xs={3}>
          <TextField
            label="計畫關鍵字"
            variant="standard"
            value={formData.keyword}
            onChange={(e)=> setFormData({...formData, keyword: e.target.value})}
          />
        </Grid>
        <Grid item xs={3}>
          <Button variant="outlined" startIcon={<AddCircleOutlineIcon />} onClick={(e)=>setFormData({...formData, projectFilters:[...formData.projectFilters, {}]})}>
            新增計畫篩選
          </Button>
        </Grid>
        {formData.projectFilters.map((x, index)=>
          <Grid item key={index} xs={12}>
            <ProjectFilterBox index={index}/>
          </Grid>
        )}

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
                 計算項目說明
               </button>
             </div>
           </>
           : <h2>查無資料</h2>}
        </Grid>

      </Grid>
      </LocalizationProvider>
    </>
  );
}

export {AppSearch};
