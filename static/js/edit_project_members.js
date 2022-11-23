$( function() {
    // preselect role

    let pk = $('input[name=pk]').val();
    $.ajax({
      type: 'GET',
      url: `/api/get_edit_info/?pk=${pk}&type=members`,
      success: function (response) {
        let i;
        for (i = 0; i < response.members.length; i++) {
            $(`#${ response.members[i].member_id }`).selectpicker('val', response.members[i].role); 
        }

      },
    })


    $('#goBack').on('click',function(){
        window.history.back();
      })
  

      $('#submitAddForm').on('click', function(){
        $('#addProjectMember').submit()
      })

      $('#submitEditForm').on('click',function(){
        $('#editProjectMember').submit()
      })

      $('#removePM').on('click',function(){
        $('#removeProjectMember').submit()
      })

})


// pass variable to modal
$(document).on("click", ".remove", function () {
     var memberid = $(this).data('id');
     $(".modal-body #memberid").val( memberid );
});
