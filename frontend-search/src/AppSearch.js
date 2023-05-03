import React, {useEffect, useState} from 'react';

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
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import InputAdornment from '@mui/material/InputAdornment';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';

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

function reducer(state, action) {
  //console.log(state,action);
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
    const formDataCleaned = cleanFormData(state.filter, state.options.deploymentDict);
    //console.log(formDataCleaned);
    if (!formDataCleaned.species) {
      dispatch({type: 'setAlert', text: '必須至少選一個物種', title:'注意'});
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
          if (data.messages) {
            //alert(data.messages);
            //if (data.redirect && data.redirect === true) {
            //  window.location.replace(window.location.origin+ "/personal_info");
            //} else {
            //console.log(document.getElementById('downloadModal'))
            $('#downloadModal').modal('show')

            const dl = document.getElementById('download-submit')
            dl.onclick = () => {
              //$('.download').on('click', function(){ // 這個會重複呼叫?
              // console.log('download!!')
              const emailInput = document.getElementById('download-email')
              const searchApiUrl = `${apiPrefix}search?filter=${d}&calc=${calc}&download=1`;
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
            $('#downloadModal').modal('hide')
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
          //alert(data.messages);
          //if (data.redirect && data.redirect === true) {
          //  window.location.replace(window.location.origin+ "/personal_info");
          //} else {
          //console.log(document.getElementById('downloadModal'))
          $('#downloadModal').modal('show')
          const formDataCleaned = cleanFormData(state.filter, state.options.deploymentDict)
          const d = JSON.stringify(formDataCleaned)
          // console.log($('.download'), 'eeee')
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
            $('#downloadModal').modal('hide')
            }
        }
      }).catch((error)=>{
        console.log('calc error:', error.message);
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
    return (
      <Box sx={{ mt: 1}}>
        <Paper elevation={2} sx={{ p: 3}}>
          <Typography variant="subtitle1">計畫篩選 ({index+1})</Typography>
          <Grid container spacing={2}>
            <Grid item xs={10}>
              <Autocomplete
                options={state.options.projects}
                getOptionLabel={(option) => option.name}
                value={state.filter.projects[index].project || null}
                groupBy={(option)=> option.group_by}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="standard"
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
                    fetchDeploymentList(v.id, newArr);
                  }
                }}
              />
            </Grid>
            <Grid item xs={2} align="right">
              <Button startIcon={<RemoveCircleOutlineIcon/>} onClick={(e)=> {
                const newArr = [...state.filter.projects];
                if (newArr.length > 1) {
                  newArr.splice(index, 1);
                  dispatch({type: 'setFilter', name: 'projects', value: newArr});
                }
                }}>
                移除
              </Button>
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
                     variant="standard"
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
                     variant="standard"
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
        </Paper>
      </Box>
    );
  };

  console.log('state', state);

  return (
    <>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={state.isLoading}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <AppSearchImageViewer setImageViewerClose={() => dispatch({type: 'setImageDetail', path: ''})} imageDetail={state.imageDetail} />
      <h3>篩選條件</h3>
      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhTW}>
      <Grid container spacing={2}>
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
            value={state.filter.startDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => dispatch({type: 'setFilter', name: 'startDate', value: v})}
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
            value={state.filter.endDate}
            inputFormat="yyyy-MM-dd"
            mask='____-__-__'
            onChange={(v) => dispatch({type: 'setFilter', name: 'endDate', value: v})}
            renderInput={(params) => <TextField {...params} variant="standard" />}
          />
        </Grid>
        <Grid item xs={3}>
          <TextField
            label="計畫關鍵字"
            variant="standard"
            value={state.filter.keyword}
            onChange={(e)=> dispatch({type: 'setFilter', name: 'keyword', value: e.target.value})}
          />
        </Grid>
        <Grid item xs={3}>
          <Button variant="outlined" startIcon={<AddCircleOutlineIcon />} onClick={(e)=>dispatch({type:'setFilter', name: 'projects', value: [...state.filter.projects, {}]})}>
            新增計畫篩選
          </Button>
        </Grid>
        {state.filter.projects.map((x, index)=>
          <Grid item key={index} xs={12}>
            <ProjectFilterBox index={index}/>
          </Grid>
        )}
        <Grid item xs={4}>
          <Box>
            <Grid container>
              <Grid item xs={6}>
                <FormControl variant="standard" sx={{ m: 1, minWidth: 120 }}>
                  <InputLabel id="demo-simple-select-standard-label">比較</InputLabel>
                  <Select
                    labelId="demo-simple-select-standard-label"
                    id="demo-simple-select-standard"
                    value={state.filter.altitudeOperator || ''}
                    onChange={(e) => dispatch({type: 'setFilter', name: 'altitudeOperator', value: e.target.value})}
                    label="比較"
                    variant="standard"
                  >
                    <MenuItem value="">-- 選擇 --</MenuItem>
                    <MenuItem value="eq">{"="}</MenuItem>
                    <MenuItem value="gt">{">="}</MenuItem>
                    <MenuItem value="lt">{"<="}</MenuItem>
                    <MenuItem value="range">{"範圍"}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl variant="standard" sx={{ m: 1}}>
                  <TextField variant="standard" label="海拔" value={state.filter.altitude || ''} onChange={(e) => dispatch({type: 'setFilter', name: 'altitude', value: e.target.value})}InputProps={{
                    endAdornment: <InputAdornment position="end">m</InputAdornment>,
                  }} helperText='範圍的話用"-"，標示，例如: 600-1200' />
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </Grid>
        <Grid item xs={2}>
          <FormControl variant="standard" sx={{ m: 1, minWidth: 200 }}>
            <Autocomplete
              multiple
              options={state.options.named_areas.county}
              getOptionLabel={(option) => option.name}
              value={state.filter.counties}
              onChange={(e, value) => { dispatch({type: 'setFilter', name: 'counties', value: value}) }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="standard"
                  label="縣市"
                />
              )}
            />
          </FormControl>
          {/*
          <TextField
            label="縣市"
            variant="standard"
            value={state.filter.county}
            onChange={(e)=> dispatch({type: 'setFilter', name: 'county', value: e.target.value})}
          />
           */}
        </Grid>
        <Grid item xs={6}>
          <FormControl variant="standard" sx={{ m: 1, marginLeft: 2, minWidth: 400 }}>
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
                  variant="standard"
                  label="保護留區"
                />
              )}
            />
          </FormControl>
          {/*
          <TextField
            label="保護留區"
            variant="standard"
            value={state.filter.protectedarea}
            onChange={(e)=> dispatch({type: 'setFilter', name: 'protectedarea', value: e.target.value})}
          />
           */}
        </Grid>
        <Grid item xs={3}>
          <Button variant="contained" onClick={handleSubmit}>搜尋</Button>
        </Grid>
        <Grid item xs={12}>
          {(state.result && state.result.data.length > 0) ?
           <>
             <AppSearchDataGrid result={state.result} handleChangePage={handleChangePage} handleChangeRowsPerPage={handleChangeRowsPerPage} pagination={state.pagination} setImageDetail={(path) => dispatch({type: 'setImageDetail', path: path})} />
             <button type="button" className="btn btn-success" onClick={handleDownload} style={{marginTop: '24px'}}>
               下載搜尋結果
             </button>
             <AppSearchCalculation calcData={state.calculation} setCalcData={dispatch} />
             <Button variant="contained" onClick={handleCalc} style={{marginTop: '10px'}}>下載計算</Button>
             {(state.alertText) ? <Alert severity="error" onClose={()=>{ dispatch({type: 'setAlert', value: ''})}}><AlertTitle>{state.alertTitle}</AlertTitle>{state.alertText}</Alert> : null}
             <div>
               <button type="button" className="btn btn-warning" data-bs-toggle="modal" data-bs-target="#exampleModal" style={{marginTop: '24px'}}>
                 計算項目說明
               </button>
             </div>
           </>
           :(state.hasSubmitted) ? <h2>查無資料</h2> : null}
        </Grid>

      </Grid>
        {VERSION}
      </LocalizationProvider>
    </>
  );
}

export {AppSearch};
