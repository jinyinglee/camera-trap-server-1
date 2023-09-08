
    $(document).on("submit", "form", function(event)
    {
        $('.loading-pop').removeClass('d-none');
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
              $('.loading-pop').addClass('d-none');
              alert('請求已送出');
              window.f_data = new FormData();

            },
            error: function (xhr, desc, err)
            {
              $('.loading-pop').addClass('d-none');
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

        if (!ValidateEmail($("input[name=email]").val())){
          checked = false
          $('input[name=email]').addClass("is-invalid");

        }  
        if (!$("input[name=q-detail-type]").is(":checked")){
          checked = false
          $('input[name=q-detail-type]').addClass("is-invalid");
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

    $('#upload-btn').click(function(){ $('#f-upload').trigger('click'); });
    $("#f-upload").change(function(){
      let f
      for (i = 0; i < this.files.length; i++) {
        window.file_index += 1;
        f = this.files[i]
        if ( ((window.f_total_size + f.size) / (1024*1024)) > 20){
          $("#f-list").append(`<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 <span class="f-remove-lg" style="">x</span></span></li>`)
        } else if ( (f.size / (1024*1024)) > 20){
          $("#f-list").append(`<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 <span class="f-remove-lg" style="">x</span></span></li>`)
        } else {
          $("#f-list").append(`<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span data-index="${window.file_index}" class="f-remove ms-2" style=""> x</span></li>`)
          var file = $('#f-upload').get(0).files[i]
          window.file_list[window.file_index] = {'file': file}
          window.f_data.append("uploaded_file", file, file.name);  
          window.f_total_size += f.size
        }
      }
      $('.f-remove').on('click', function(){        
        delete window.file_list[$(this).data('index')]
        // delete from FormData
        window.f_data.delete('uploaded_file')
        window.f_total_size = 0
        // re-append to FormData
        Object.entries(window.file_list).forEach(([k,v]) => {
          window.f_data.append("uploaded_file", v['file'], v['file'].name);  
          window.f_total_size += v['file'].size
        })

        console.log(window.f_total_size)
        $(this).parent().remove()
      })
      $('.f-remove-lg').on('click', function(){
        $(this).parent().parent().remove()
      })
    });
    
    //https://emailregex.com
    function ValidateEmail(inputText) {
      let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/;
      if (inputText.match(mailformat)) {
        return true
      } else {
        return false
      }
    }
