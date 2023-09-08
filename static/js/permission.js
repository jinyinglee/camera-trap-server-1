
  $('#goBack').on('click',function(){
    window.history.back();
  })
  
  // pass variable to modal
  $(document).on("click", ".remove", function () {
      var id = $(this).data('id');
      var type = $(this).data('type');
      $(".modal-body #id").val( id );
      $(".modal-body #type").val( type );
  });
  

  $('#submitAddForm').on('click',function(){
    $('#addOrgAdmin').submit();
  })
  
  
  $('#removeBtnClick').on('click',function(){
    $('#removeBtn').submit()
  })

$('#addOrgProjectClick').on('click', function(){
    $('#addOrgProject').submit()
})

if ($('input[name=return_message]').val()!=''){
  alert($('input[name=return_message]').val())
}


