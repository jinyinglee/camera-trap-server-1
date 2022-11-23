


$(document).ready(function() {

  $('.setModal').on('click', function(){    
    let deployment_journal_id = $(this).data('deployment_journal_id');
    let species_error = $(this).data('species_error');
    let upload_error = $(this).data('upload_error');
      $('.error-link').attr("href", "/get_error_file_list/" + deployment_journal_id );
      species_error=='True' ? $('.species-error').show() : $('.species-error').hide()
      upload_error=='True' ? $('.upload-error').show() : $('.upload-error').hide()
  
    $('#errorModal').modal('show')

  })
  
  
  
})