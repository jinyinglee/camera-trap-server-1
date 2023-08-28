import { format } from 'date-fns'

const cleanFormData = (formData, depOptions, isVerbose) => {
  let cleaned = {};
  /*if (isVerbose === true) {
    cleaned['verbose'] = formData;
  }
  */

  for (const v in formData) {
    if (v === 'species') {
      if (formData[v].length > 0) {
        cleaned[v] = formData[v].map(x=>x.name);
      }
    } else if (v === 'projects_depricated') {
      if (formData[v].length > 0) {
        cleaned[v] = formData[v].map(x=>x.id);
      }
    } else if (['startDate', 'endDate'].indexOf(v) >= 0 && formData[v] != null) {
      cleaned[v] = format(formData[v], 'yyyy-MM-dd');
    } else if ( v === 'projects') {
      let projects = [];
      for (const i in formData['projects']) {
        if (formData['projects'][i].hasOwnProperty('project') && formData['projects'][i].project !== null) {
          if (formData['projects'][i].hasOwnProperty('deployments') && formData['projects'][i].deployments.length > 0) {
            const deployments = formData['projects'][i].deployments.map(x => {
              return ({
                id: x.deployment_id,
                name: x.name,
                studyarea_name: x.groupBy,
              })
            })
            projects.push({
              deployments: deployments,
              project: formData['projects'][i].project,
            })
          } else if (formData['projects'][i].hasOwnProperty('studyareas') && formData['projects'][i].studyareas.length > 0) {
            const studyareas = formData['projects'][i].studyareas.map(x => ({
              id: x.studyarea_id,
              name: x.name,
            }))
            projects.push({
              studyareas: studyareas,
              project: formData['projects'][i].project,
            })
          }
          else if (formData['projects'][i].hasOwnProperty('project')) {
            projects.push({
              project: {
                id: formData['projects'][i].project.id,
                name: formData['projects'][i].project.name,
              }
            })
          }
        }
      }
      if (projects.length >= 0) {
        cleaned['projects'] = projects
      }
    } else if (formData[v]) {
      // other
      cleaned[v] = formData[v];
    }
  }
  return cleaned
}

// from django sample code
const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export {cleanFormData, getCookie};
