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
      for (const i in formData['projects']) {
        deploymentIds = deploymentIds.concat(formData['projects'][i].deploymentIds);
        /*
        if (formData['projects'][i].deployments && formData['projects'][i].deployments.length > 0) {
          //cleaned['deployments'] = formData['projects'][i].deployments.map(x=>x.deployment_id);
          cleaned['deployments'] = formData['projects'][i].deploymentIds;
        } else if (formData[v][i].studyareas && formData[v][i].studyareas.length > 0) {
          for (const j in formData['projects'][i].studyareas) {
            //cleaned['studyareas'] = formData['projects'][i].studyareas.map(x=>x.studyarea_id);
            cleaned['studyareas'] = formData['projects'][i].studyareaIds;
          }
        } else {
          //cleaned['projects'] = formData['projects'].filter((x)=> x.project && x.project.id).map(x => x.project.id);
          //console.log()
          if (cleaned['projects'].length <= 0) {
            delete cleaned.projects
          }
        }
        */
      }
      cleaned['deployments'] = deploymentIds;
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
