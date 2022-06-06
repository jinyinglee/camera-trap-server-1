import { format } from 'date-fns'

const cleanFormData = (formData, depOptions) => {
  let cleaned = {};
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
      let deploymentIds = [];
      // console.log(formData);
      for (const i in formData['projects']) {
        if (formData['projects'][i].project !== null) {
          const projectId = formData['projects'][i].project.id;
          if (formData['projects'][i].hasOwnProperty('deployments') && formData['projects'][i].deployments.length > 0) {
            deploymentIds = deploymentIds.concat(formData['projects'][i].deployments.map(x => x.deployment_id));
          } else if (formData['projects'][i].hasOwnProperty('studyareas') && formData['projects'][i].studyareas.length > 0) {
            for (const j in formData['projects'][i].studyareas) {
              const foundIndex = depOptions[projectId].findIndex( x => x.studyarea_id === formData['projects'][i].studyareas[j].studyarea_id);
              if (foundIndex >= 0) {
                const values = depOptions[projectId][foundIndex].deployments.map(x => x.deployment_id);
                deploymentIds = deploymentIds.concat(values);
              }
            }
          } else if (formData['projects'][i].hasOwnProperty('project')) {
            for (const sa in depOptions[projectId]) {
              const values = depOptions[projectId][sa].deployments.map(x => x.deployment_id);
              deploymentIds = deploymentIds.concat(values);
            }
          }
        }
      }
      cleaned['deployments'] = deploymentIds;
      if (cleaned['deployments'].length <= 0) {
        delete cleaned.deployments
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
