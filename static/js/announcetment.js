
    $(document).on("submit", "form", function(event)
    {
        $('.loader').removeClass('d-none');
        event.preventDefault();
        
        let otherFormData = new FormData($("#submitForm")[0]);
        for (var pair of otherFormData.entries()) {
          window.f_data.append(pair[0], pair[1]);
        }
        
        $.ajax({
            url: $(this).attr("action"),
            type: $(this).attr("method"),
            dataType: "JSON",
            data: window.f_data,
            processData: false,
            contentType: false,
            success: function (data, status)
            {
              $('.loader').addClass('d-none');
              alert('請求已送出');
              window.f_data = new FormData();

            },
            error: function (xhr, desc, err)
            {
              $('.loader').addClass('d-none');
              alert('未知錯誤，請聯繫管理員');
              window.f_data = new FormData();
            }
        });        
    
    });

    $(document).ready(

      $('.submit').on('click', function(){
        // clear previous validation
        $('.is-invalid').removeClass("is-invalid")
        let checked = true
        if ($('textarea[name=announcement-title]').val()==''){
          checked = false
          $('textarea[name=announcement-title]').addClass("is-invalid");
        } 
        if ($('textarea[name=description]').val()==''){
          checked = false
          $('textarea[name=description]').addClass("is-invalid");
        }  
        if ($('#g-recaptcha-response').val()==''){
          checked = false
          $('.g-recaptcha').addClass("is-invalid");
        }
        
        if (checked) {
        $('#submitForm').submit()
        }
      })
        
    );
    
    window.file_list = {}
    window.file_index = 0
    window.f_data = new FormData()
    window.f_total_size = 0
