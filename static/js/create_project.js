$(document).ready(function () {
    $(".datepicker").datepicker({
      dateFormat: "yy-mm-dd",
    });

    $(".datepicker_publish").datepicker({
      dateFormat: "yy-mm-dd",
      defaultDate: "+5y",
    });
  });


  $('#validateForm').on('click',function(){
    // name
    let name = $('[name="name"]');
    if (name.val() == "") {
      name.addClass("is-invalid").addClass("was-validated");
    } else {
      name.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
    }

    // principal_investigator
    let pi = $('[name="principal_investigator"]');
    if (pi.val() == "") {
      pi.addClass("is-invalid").addClass("was-validated");
    } else {
      pi.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
    }

    // start_date
    let start_date = $('[name="start_date"]');
    if (start_date.val() == "") {
      start_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", start_date.val());
        start_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        start_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    // end_date
    let end_date = $('[name="end_date"]');

    if (end_date.val() == "") {
      end_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", end_date.val());
        end_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        end_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    if (!$(".is-invalid").length) {
      $("#first-page").hide();
      $("#second-page").show();
      window.location.hash = "#second-page";
      window.location.href = "#second-page";
    } else {
      $(".is-invalid").first().attr("id", "invalid");
      window.location.href = "#invalid";
      window.location.hash = "#invalid";
    }

  })


  $('#submitForm').on('click', function(){
    // publish_date

    let check = [];
    let publish_date = $('[name="publish_date"]');

    if (publish_date.val() == "") {
      publish_date.addClass("is-invalid").addClass("was-validated");
      check.push(false);
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", publish_date.val());
        publish_date.removeClass("is-invalid").removeClass("was-validated");
      } catch (error) {
        publish_date.addClass("is-invalid").addClass("was-validated");
        check.push(false);
      }
    }

    if (!$(".is-invalid").length) {
      $("#createProjectForm").submit();
    }

})

