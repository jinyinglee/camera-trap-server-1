import { format } from 'date-fns'

const cleanFormData = (formData) => {
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
      const studyareaIds = [];
      const deploymentIds = [];
      for (const i in formData['projects']) {
        if (formData['projects'][i].deployments && formData['projects'][i].deployments.length > 0) {
          cleaned['deployments'] = formData['projects'][i].deployments.map(x=>x.deployment_id);
        } else if (formData[v][i].studyareas && formData[v][i].studyareas.length > 0) {
          cleaned['studyareas'] = formData['projects'][i].studyareas.map(x=>x.studyarea_id);
        } else {
          cleaned['projects'] = formData['projects'].map(x => x.project.id);
        }
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
