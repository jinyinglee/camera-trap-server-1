$(document).ready(function () {
    $(".datepicker_publish").datepicker({
      dateFormat: "yy-mm-dd",
      defaultDate: "+5y",
    });

    // precheck license
    let pk = $('input[name=pk]').val();
    $.ajax({
      type: 'GET',
      url: `/api/get_edit_info/?pk=${pk}&type=license`,
      success: function (response) {
        $(`[name="interpretive_data_license"][value="${ response.interpretive_data_license }"]`).attr("checked", "checked");
        $(`[name="identification_information_license"][value="${ response.identification_information_license }"]`).attr("checked", "checked");
        $(`[name="video_material_license"][value="${ response.video_material_license }"]`).attr("checked", "checked");
      },
    })


 
 
    $('#goBack').on('click',function(){
      window.history.back();
    })
  

  // validation
  $('#submitForm').on('click', function(){
    // publish_date
    let publish_date = $('[name="publish_date"]');

    if (publish_date.val() == "") {
      publish_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", publish_date.val());
        publish_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        publish_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    if (!$(".is-invalid").length) {
      $("#editProjectLicense").submit();
    } else {
      $(".is-invalid").first().attr("id", "invalid");
      window.location.href = "#invalid";
      window.location.hash = "#invalid";
    }

  })


  });

