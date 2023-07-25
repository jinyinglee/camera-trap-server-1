import React, {useEffect, useState} from 'react';

import { createTheme, ThemeProvider } from '@mui/material/styles';
import Chip from '@mui/material/Chip';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import Backdrop from '@mui/material/Backdrop';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import CircularProgress from '@mui/material/CircularProgress';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline';
import SearchIcon from '@mui/icons-material/Search';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import InputAdornment from '@mui/material/InputAdornment';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import IconButton from '@mui/material/IconButton';

import { zhTW } from 'date-fns/locale';

import { AppSearchDataGrid } from './AppSearchDataGrid';
import { AppSearchImageViewer} from './AppSearchImageViewer';
import { AppSearchCalculation } from './AppSearchCalculation';
import { cleanFormData } from './Utils';
import { VERSION } from './Version'

const DEFAULT_PER_PAGE = 20;
const initialState = {
  filter: {
    species: [],
    startDate: new Date(2014, 0, 1),
    endDate: new Date(),
    projects: [{project: null}],
    counties: [],
    protectedareas: [],
    keyword: '',
    altitudeOperator: 'eq',
  },
  pagination: {
    pageIndex: 0,
    perPage: DEFAULT_PER_PAGE,
  },
  options: {
    species: [],
    projects: [],
    named_areas: {
      county: [],
      protectedarea: [],
    },
    deploymentDict: null,
  },
  isLoading: false,
  isSubmitted: false,
  alertText: '',
  alertTitle: '',
  result: null,
  calculation: {
    session: 'month',
    imageInterval: '60',
    eventInterval: '60',
    fileFormat: 'excel',
    calcType: 'basic-oi',
  },
  imageDetail: '', // replace with path to open image viewer dialog
};

const theme = createTheme({
  palette: {
    primary: {
      main: '#59AE68'
    },
    secondary: {
      main: '#11cb5f',
    },
  },
});

function reducer(state, action) {
  switch (action.type) {
  case 'startLoading':
    return {
      ...state,
      isLoading: true,
      isInit: false
    };
  case 'stopLoading':
    return {
      ...state,
      isLoading: false,
      alertText: action.text || null,
      alertTitle: action.title || null,
    };
  case 'initOptions':
    return {
      ...state,
      options: {
        ...state.options,
        projects: action.value.projects,
        species: action.value.species,
        named_areas: action.value.named_areas,
      },
      isInit: true,
    };
  case 'setDeploymentFilter':
    // update option & filter
    return {
      ...state,
      options: {
        ...state.options,
        deploymentDict: action.value,
      },
      filter: {
        ...state.filter,
        projects: action.projects,
      },
      isLoading: false,
    }
  case 'setFilter':
    return {
      ...state,
      filter: {
        ...state.filter,
        [action.name]: action.value
      },
      pagination: {
        pageIndex: 0,
        perPage: state.pagination.perPage,
      }
    }
  case 'setResult':
    return {
      ...state,
      result: action.value,
      isLoading: false,
      hasSubmitted: true,
    }
  case 'setPagination':
    return {
      ...state,
      pagination: {
        pageIndex: action.pageIndex,
        perPage: action.perPage,
      }
    }
  case 'setAlert':
    return {
      ...state,
      alertText: action.text,
      alertTitle: action.title,
    }
  case 'setCalcData':
    return {
      ...state,
      calculation: {
        ...state.calculation,
        [action.name]:  action.value,
      }
    }
  case 'setImageDetail':
    return {
      ...state,
      imageDetail: action.path,
    }
  default:
    //throw new Error();
    console.error('reducer errr!!!');
  }
}

const fetchOptions = async (urls) => {
  try {
    const response = await Promise.all(
      urls.map(url => fetch(url).then(res => res.json()))
    )
    return response
  } catch (error) {
    console.log("Error", error)
  }
}


const AppSearch = () => {
  const today = new Date();
  const todayYMD = `${today.getFullYear()}-${today.getMonth().toString().padStart(2, '0')}-${today.getDay().toString().padStart(2, '0')}`;
  //console.log(todayYMD);
  const apiPrefix = process.env.API_URL;
  const [state, dispatch] = React.useReducer(reducer, initialState);

  useEffect(() => {
    const urls = [
      `${apiPrefix}species`,
      `${apiPrefix}projects`,
      `${apiPrefix}named_areas`,
    ]
    let options = {};
    fetchOptions(urls).then( resp => {
      resp.forEach( x => {
        if (x.category == 'named_areas') {
          options.named_areas = x.data
        } else {
          options[x.category] = x.data
        }
      })
      dispatch({type: 'initOptions', value: options});
    })
  }, []);

  //useEffect(() => {
  //}, []);

  const fetchData = (props) => {
    const formDataCleaned = cleanFormData(state.filter, state.options.deploymentDict);
    console.log('cleaned', formDataCleaned);
    //const csrftoken = getCookie('csrftoken');
    const d = JSON.stringify(formDataCleaned);
    let searchApiUrl = `${apiPrefix}search?filter=${d}`;

    let pagination = {};
    if (props && props.hasOwnProperty('perPage') && props.hasOwnProperty('pageIndex')) {
      pagination = {...props};
    } else if (state.pagination.perPage === 10) {
      pagination = { pageIndex: 0, perPage: DEFAULT_PER_PAGE };
    } else {
      pagination = state.pagination;
    }
    searchApiUrl = `${searchApiUrl}&pagination=${JSON.stringify(pagination)}`;

    dispatch({type: 'startLoading'});
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
        dispatch({type: 'setResult', value: data});
      }).catch((error) => {
        console.log('fetchData error: ', error.message);
        dispatch({type: 'stopLoading', text: error.message, title: 'server_err'});
      });
  };

  const fetchDeploymentList = (projectId, projects) => {
    let studyareaApiUrl = `${apiPrefix}deployments?project_id=${projectId}`;

    dispatch({type: 'startLoading'});
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
        let newDeploymentDict = state.options.deploymentDict || {};
        newDeploymentDict[projectId] = data.data;
        dispatch({type: 'setDeploymentFilter', value: newDeploymentDict, projects: projects});
      }).catch((error) => {
        console.log('fetchDeploymentList error: ', error.message);
        dispatch({type: 'stopLoading', text: error.message, title: 'server err'});
      });

        dispatch({type: 'startLoading'});
  };

  const handleSubmit = () => {
    fetchData();
  }

  const handleChangePage = (e, pageIndex) => {
    const pp = (state.pagination.perPage === 10) ? 20 : state.pagination.perPage;
    dispatch({type:'setPagination', pageIndex: pageIndex, perPage: pp});
    fetchData({pageIndex: pageIndex, perPage: pp});
  }

  const handleChangeRowsPerPage = (e) => {
    const perPage = parseInt(e.target.value, 10);
    dispatch({type:'setPagination', pageIndex: 0, perPage: perPage});
    fetchData({pageIndex:0, perPage: perPage});
  }

  const handleCalc = () => {
    const formDataCleaned = cleanFormData(state.filter, state.options.deploymentDict, true);
    //console.log(formDataCleaned);
    if (!formDataCleaned.species) {
      dispatch({type: 'setAlert', text: '必須至少選一個物種', title:'注意'});
      setTimeout(()=> {
        dispatch({type: 'setAlert', text: '', title:''});
      }, 3000)
    } else {
      const calc = JSON.stringify(state.calculation);
      const d = JSON.stringify(formDataCleaned);
      /*
      const searchApiUrl = `${apiPrefix}search?filter=${d}&calc=${calc}&download=1`;
      dispatch({type: 'startLoading'});
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
          const ext_name = (state.calculation.fileFormat === 'csv') ? 'csv' : 'xlsx';
          // code via: https://stackoverflow.com/a/65609170/644070
          const href = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = href;
          link.setAttribute('download', `camera-trap-calculation-${state.calculation.calcType}.${ext_name}`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          dispatch({type:'stopLoading'});
        }).catch((error)=>{
          console.log('calc error:', error.message);
          dispatch({type: 'stopLoading', text: error.message, title: 'server err'});
        });
      */
      const searchApiUrl = `${apiPrefix}check_login/`;
      console.log('fetch:', searchApiUrl);
      fetch(encodeURI(searchApiUrl), {
        mode: 'same-origin',
        headers: {
          'content-type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest', // for Django request.is_ajax()
          //'X-CSRFToken': csrftoken,
        },
        method: 'GET',
      })
        .then(resp => resp.json())
        .then( data => {
          console.log('check_login', data);
          if (data.messages) {
            alert(data.messages);
            if (data.redirect && data.redirect === true) {
              window.location.replace(window.location.origin+ "/personal_info");
            }
          } else {
            //$('#downloadModal').modal('show')
            $('.down-pop').fadeIn();
            const dl = document.getElementById('download-submit')
            dl.onclick = () => {
                //$('.download').on('click', function(){ // 這個會重複呼叫?
                // console.log('download!!')
                const emailInput = document.getElementById('download-email')
                const searchApiUrl = `${apiPrefix}search?filter=${d}&email=${emailInput.value}&calc=${calc}&download=1`;
                console.log('fetch:', searchApiUrl);
                fetch(encodeURI(searchApiUrl), {
                  mode: 'same-origin',
                  headers: {
                    'content-type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest', // for Django request.is_ajax()
                    //'X-CSRFToken': csrftoken,
                  },
                method: 'GET',
                })
                  .then( resp => resp.json() )
                  .then( data2 => {
                    console.log(data2);
                  })
                  .catch( error => {
                    console.log('downloadData error:', error.message);
                  })
                //$('#downloadModal').modal('hide')
                $('.down-pop').fadeOut();
                alert('請求已送出');
              }
          }
        }).catch((error)=>{
          console.log('calc error:', error.message);
        });
    }
  }

  const handleDownload = () => {
    const searchApiUrl = `${apiPrefix}check_login/`;

    console.log('fetch:', searchApiUrl);
    fetch(encodeURI(searchApiUrl), {
      mode: 'same-origin',
      headers: {
        'content-type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // for Django request.is_ajax()
        //'X-CSRFToken': csrftoken,
      },
      method: 'GET',
    })
      .then(resp => resp.json())
      .then( data => {
        if (data.messages) {
          alert(data.messages);
          if (data.redirect && data.redirect === true) {
            window.location.replace(window.location.origin+ "/personal_info");
          }
        } else {
          $('.down-pop').fadeIn();
          const formDataCleaned = cleanFormData(state.filter, state.options.deploymentDict, true)
          const d = JSON.stringify(formDataCleaned)
          const dl = document.getElementById('download-submit')
          dl.onclick = () => {
            //$('.download').on('click', function(){ // 這個會重複呼叫?
            // console.log('download!!')
            const emailInput = document.getElementById('download-email')
            const searchApiUrl = `${apiPrefix}search?filter=${d}&email=${emailInput.value}&downloadData=1`;
            console.log('fetch:', searchApiUrl);

            fetch(encodeURI(searchApiUrl), {
              mode: 'same-origin',
              headers: {
                'content-type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest', // for Django request.is_ajax()
                //'X-CSRFToken': csrftoken,
              },
              method: 'GET',
            })
              .then( resp => resp.json() )
              .then( data2 => {
                console.log(data2);
              })
              .catch( error => {
                console.log('downloadData error:', error.message);
              })
            //$('#downloadModal').modal('hide')
            $('.down-pop').fadeOut();
            alert('請求已送出');
          }
        }
      }).catch((error)=>{
        console.log('download error:', error.message);
      });
  }

  const ProjectFilterBox = ({index}) => {
    const projectId = (state.filter.projects[index].project) ? state.filter.projects[index].project.id : null;
    const studyareas = state.filter.projects[index].studyareas || [];
    let deploymentOptions = [];
    for (let i in studyareas) {
      const values = studyareas[i].deployments.map(x=> {x.groupBy = studyareas[i].name; return x});
      deploymentOptions = deploymentOptions.concat(values);
    }
    const circleNumStyle = {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: '#257455',
      color: '#FFF',
      width: '30px',
      height: '30px',
      borderRadius: '50%',
      flex: '0 0 30px',
      marginLeft: '5px',
    }
    return (
      <Box sx={{ mt: 1}}>
        <Grid sx={{ background: '#f7f7f7', borderRadius: '20px', padding: '20px 20px 5px 20px', marginBottom: '20px', position: 'relative'}} container>
          <Grid container sx={{ alignItems: 'center', marginBottom: '20px'}} >
            <Grid container item xs={6}>
              <Typography sx={{ fontSize: '20px', fontWeight: 'normal' }} variant="span">計畫篩選 </Typography>
              <Box component="span" sx={circleNumStyle}>{index+1}</Box>
            </Grid>
            <Grid item xs={6} align="right">
              <IconButton color="primary" onClick={(e)=> {
                const newArr = [...state.filter.projects];
                if (newArr.length > 1) {
                  newArr.splice(index, 1);
                  dispatch({type: 'setFilter', name: 'projects', value: newArr});
                }
              }}>
                <RemoveCircleOutlineIcon />
              </IconButton>
            </Grid>
          </Grid>
          <Grid container spacing={2} sx={{ marginBottom: '20px'}}>
            <Grid item xs={12}>
              <Autocomplete
                options={state.options.projects}
                getOptionLabel={(option) => option.name}
                value={state.filter.projects[index].project || null}
                groupBy={(option)=> option.group_by}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    label="計畫名稱"
                  />
                )}
                onChange={(e, v) => {
                  const newArr = [...state.filter.projects];
                  if (v === null) {
                    newArr[index] = {};
                    dispatch({type: 'setFilter', name: 'projects', value: newArr});
                  } else {
                    newArr[index].project = v;
                    newArr[index].studyareas = [];
                    fetchDeploymentList(v.id, newArr);
                  }
                }}
              />
            </Grid>
            {(state.filter.projects[index].project && state.options.deploymentDict && state.options.deploymentDict[projectId]) ?
             <Grid item xs={6}>
               <Autocomplete
                 multiple
                 options={state.options.deploymentDict[projectId]}
                 getOptionLabel={(option) => option.name}
                 value={state.filter.projects[index].studyareas || []}
                 renderInput={(params) => (
                   <TextField
                     {...params}
                     variant="outlined"
                     label="樣區"
                   />
                 )}
                 onChange={(e, v) => {
                   const newArr = [...state.filter.projects];
                   newArr[index].studyareas = v;
                   const studyareaIds = [];
                   //const deploymentIds = [];
                   //for(const i in v) {
                   //  studyareaIds.push(v[i].studyarea_id);
                   //  for (const j in v[i].deployments) {
                   //    deploymentIds.push(v[i].deployments[j].deployment_id);
                   //  }
                   //}
                   //newArr[index].studyareaIds = studyareaIds;
                   //newArr[index].deploymentIds = deploymentIds;
                   dispatch({type:'setFilter', name:'projects', value:newArr});
                 }}
               />
             </Grid>
             : null}
            {(state.filter.projects[index].project && state.options.deploymentDict && state.filter.projects[index].studyareas && state.filter.projects[index].studyareas) ?
             <Grid item xs={6}>
               <Autocomplete
                 multiple
                 options={deploymentOptions}
                 getOptionLabel={(option) => `${option.groupBy}: ${option.name}`}
                 value={state.filter.projects[index].deployments || []}
                 groupBy={(option)=> option.groupBy}
                 renderInput={(params) => (
                   <TextField
                     {...params}
                     variant="outlined"
                     label="相機位置"
                   />
                 )}
                 onChange={(e, v) => {
                   const newArr = [...state.filter.projects];
                   newArr[index].deployments = v;
                   //newArr[index].deploymentIds = v.map((x)=>x.deployment_id);
                   dispatch({type: 'setFilter', name: 'projects', value: newArr});
                 }}
               />
             </Grid>
             : null}
          </Grid>
        </Grid>
      </Box>
    );
  };

  console.log('state', state);

  const BoxStyle = {
    fontSize: '24px',
    background: '#FFF',
    borderRadius: '15px',
    boxShadow: '0 0 8px rgba(0,0,0,0.08)',
    padding: '25px 20px'
  }
  return (
    <>
      <ThemeProvider theme={theme}>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={state.isLoading}
      >
    {/*<CircularProgress color="inherit" />*/}
    <div className="loader"></div>
      </Backdrop>
      <AppSearchImageViewer setImageViewerClose={() => dispatch({type: 'setImageDetail', path: ''})} imageDetail={state.imageDetail} />
      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhTW}>
        <Grid container spacing={2} sx={BoxStyle}>
          <Grid item xs={12}>
            <Typography sx={{
              fontSize: '24px',
              color: '#59AE68',
            }}>篩選條件</Typography>
          </Grid>
          <Grid item xs={3}>
          <Autocomplete
            multiple
            freeSolo
            filterSelectedOptions
            options={state.options.species}
            getOptionLabel={(option) => option.name}
            value={state.filter.species}
            inputValue={state.filter.speciesText || ''}
            onChange={(e, value) => dispatch({type: 'setFilter', name: 'species', value: value})}
            onInputChange={(e, value, reason) => {
              console.log('inputch', value, reason);
              if (reason === 'input') {
                dispatch({type: 'setFilter', name: 'speciesText', value: value});
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="outlined"
                label="物種"
              />
            )}
    ChipProps={{ color: 'primary', variant: 'outlined' }}
          />
        </Grid>
        <Grid item xs={3}>
          <DatePicker
            disableFuture
            label="資料啟始日期"
            openTo="year"
            clearable={true}
            views={['year', 'month', 'day']}
            value={state.filter.startDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => dispatch({type: 'setFilter', name: 'startDate', value: v})}
            renderInput={(params) => <TextField {...params} variant="outlined"/>}
          />
        </Grid>
        <Grid item xs={3}>
          <DatePicker
            disableFuture
            label="資料結束日期"
            clearable={true}
            openTo="year"
            views={['year', 'month', 'day']}
            value={state.filter.endDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => dispatch({type: 'setFilter', name: 'endDate', value: v})}
            renderInput={(params) => <TextField {...params} variant="outlined" />}
          />
        </Grid>
        <Grid item xs={3}>
          <TextField
            label="計畫關鍵字"
            variant="outlined"
            value={state.filter.keyword}
            onChange={(e)=> dispatch({type: 'setFilter', name: 'keyword', value: e.target.value})}
          />
        </Grid>
        {state.filter.projects.map((x, index)=>
          <Grid item key={index} xs={12}>
            <ProjectFilterBox index={index}/>
          </Grid>
        )}
        <Grid item xs={12}>
          <Grid container justifyContent="center">
            <Button variant="outlined" endIcon={<AddCircleOutlineIcon />} onClick={(e)=>dispatch({type:'setFilter', name: 'projects', value: [...state.filter.projects, {}]})} sx={{ borderRadius: '25px'}} size="large">
              新增計畫篩選
            </Button>
          </Grid>
        </Grid>
        <Grid item xs={12}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              海拔
            </Grid>
            <Grid item xs={1}>
                <Select
                  fullWidth
                  labelId="demo-simple-select-standard-label"
                  id="demo-simple-select-standard"
                  value={state.filter.altitudeOperator || 'eq'}
                  onChange={(e) => dispatch({type: 'setFilter', name: 'altitudeOperator', value: e.target.value})}
                  label="比較"
                  variant="outlined"
                >
                  <MenuItem value="">-- 選擇 --</MenuItem>
                  <MenuItem value="eq">{"="}</MenuItem>
                  <MenuItem value="gt">{">="}</MenuItem>
                  <MenuItem value="lt">{"<="}</MenuItem>
                  <MenuItem value="range">{"範圍"}</MenuItem>
                </Select>
            </Grid>
            <Grid item xs={5}>
                  <TextField fullWidth variant="outlined" label="" value={state.filter.altitude || ''} onChange={(e) => dispatch({type: 'setFilter', name: 'altitude', value: e.target.value})} InputProps={{
                    endAdornment: <InputAdornment position="end">m</InputAdornment>,
                  }} />
            </Grid>
            <Grid item xs={6}>
              <Typography sx={{
                fontSize: '16px',
                color: '#888',
                marginLeft: '15px',
                height: '50px',
                lineHeight: '50px'
              }}>範圍的話用"-"，標示，例如: 600-1200</Typography>
            </Grid>
            <Grid item xs={6}>
              縣市
            </Grid>
            <Grid item xs={6}>
              保護留區
            </Grid>
            <Grid item xs={6}>
              <Autocomplete
                multiple
                options={state.options.named_areas.county}
                getOptionLabel={(option) => option.name}
                value={state.filter.counties}
                onChange={(e, value) => { dispatch({type: 'setFilter', name: 'counties', value: value}) }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    label="縣市"
                  />
                )}
              />
            </Grid>
            <Grid item xs={6}>
              <Autocomplete
                multiple
                options={state.options.named_areas.protectedarea}
                getOptionLabel={(option) => option.name}
                value={state.filter.county}
                onChange={(e, value) => dispatch({type: 'setFilter', name: 'protectedareas', value: value})}
                groupBy={(option) => option.category}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    label="保護留區"
                  />
                )}
              />
            </Grid>
          </Grid>
        </Grid>
        <Grid item xs={12} align="center">
          <Button variant="contained" onClick={handleSubmit} endIcon={<SearchIcon />} sx={{ borderRadius: '25px', background: '#59AE68', color: '#FFFFFF', width: '180px'}} size="large">搜尋</Button>
        </Grid>
        <Grid item xs={12} align="center">
          {(state.result && state.result.data.length > 0) ?
           <>
             <AppSearchDataGrid result={state.result} handleChangePage={handleChangePage} handleChangeRowsPerPage={handleChangeRowsPerPage} pagination={state.pagination} setImageDetail={(path) => dispatch({type: 'setImageDetail', path: path})} />
             <Button variant="contained" onClick={handleDownload} sx={{ borderRadius: '25px', background: '#59AE68', color: '#FFFFFF', width: '180px', marginTop: '20px' }} size="large">下載搜尋結果</Button>
             <AppSearchCalculation calcData={state.calculation} setCalcData={dispatch} />
             <Button variant="outlined" sx={{ borderRadius: '25px', width: '180px', marginTop: '20px', marginRight: '8px' }} size="large" data-bs-toggle="modal" data-bs-target="#exampleModal">計算項目說明</Button>
             <Button variant="contained" onClick={handleCalc} sx={{ borderRadius: '25px', width: '180px', background: '#59AE68', color: '#FFFFFF', marginTop: '20px', marginLeft: '8px' }} size="large">下載計算</Button>
             {(state.alertText) ? <Alert severity="error" onClose={()=>{ dispatch({type: 'setAlert', value: ''})}}><AlertTitle>{state.alertTitle}</AlertTitle>{state.alertText}</Alert> : null}
           </>
           :(state.hasSubmitted) ? <h2>查無資料</h2> : null}
        </Grid>
          <Grid item xs={12} align="right">
            <Typography variant="body2" color="grey.300">{VERSION}</Typography>
          </Grid>
      </Grid>
    </LocalizationProvider>
    </ThemeProvider>
    </>
  );
}

export {AppSearch};
