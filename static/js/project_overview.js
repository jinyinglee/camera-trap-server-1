var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $publicproject = $('#publicproject-tbody').html()
var $myproject = $('#myproject-tbody').html()

$(function () {


	$('.upar1').on('click', function() {
		$(this).css("fill", "#257455");
		$('.dwar1').css("fill", "#ADDBB9");
	});
	$('.dwar1').on('click', function() {
		$(this).css("fill", "#257455");
		$('.upar1').css("fill", "#ADDBB9");
	});
	$('.settitle-box').on('click', function() {
		$(this).next('.check-list').slideToggle();
		$(this).toggleClass('now');

	});
	$('.opitem-btn').on('click', function() {
		if($('.left-selectlist').css("left") == "0px"){
			$('.left-selectlist').animate({
				left: "-300"
			});
		}else{
			$('.left-selectlist').animate({
				left: "0"
			});
		}
	});


  // species: if other checkbox checked, uncheck 'all'
  /*
  $("input[name='species-filter'].filter:not(.all)").click(function () {
    let table_id = $(".col-10 .active").attr("aria-controls");
    if ($(this).is(":checked")) {
      $('<i class="fas fa-check title-dark w-12"></i>').insertBefore($(this));
    } else {
      $(this).parent("label").children("svg").remove();
    }
    $(`input[name='species-filter'].all.${table_id}`).prop("checked", false);
    $(`#species-list-all-${table_id} label`).children("svg").remove();
  });*/

  $('.species-check-list li:not(.all)').click(function(){
    $(this).toggleClass('now')
    let list_name = $(this).data('table')
    $(`.species-check-list li.all[data-table=${list_name}]`).removeClass('now')
  })

  // species: if 'all' checked, check all checkbox

  $('.species-check-list li.all').click(function(){

    /*
    let table_id = $(".pj-tab li.now").data('table');
    let list_name;
    if (table_id == "publicproject") {
      list_name = "public-species";
    } else {
      list_name = "my-species";
    }*/

    let list_name = $(this).data('table')

    if ($(this).hasClass('now')) {
      // 移除掉全部的
      $(this).removeClass('now')
      $(`.species-check-list li[data-table=${list_name}]`).removeClass('now')
    } else {
      // 先移除掉全部的再一次加上去
      $(this).removeClass('now')
      $(`.species-check-list li[data-table=${list_name}]`).removeClass('now')
      $(this).addClass('now')
      $(`.species-check-list li[data-table=${list_name}]`).addClass('now')
    }

  })

  /*
  $("input[name='species-filter'].all").click(function () {
    let table_id = $(".col-10 .active").attr("aria-controls");
    let list_name;
    if (table_id == "publicproject") {
      list_name = "public-species";
    } else {
      list_name = "my-species";
    }
    if ($(this).is(":checked")) {
      // 先移除掉全部的再一次加上去
      $(`#species-list li.${list_name} label`).children("svg").remove();
      $(`#species-list li.${list_name} label`).prepend('<i class="fas fa-check title-dark w-12"></i>');
      $(`input[name='species-filter'].${table_id}`).prop("checked", true);
    } else {
      $(`#species-list li.${list_name} label`).children("svg").remove();
      $(`input[name='species-filter'].${table_id}`).prop("checked", false);
    }
  });*/

  // 切換左側物種統計欄
  // speices filter list
  $(".pj-tab li").on("click", function () {

    $(".pj-tab li").removeClass('now')
    $(this).addClass('now')

    if ($(this).data('table') == 'publicproject'){
      $("li[data-table=public-species]").removeClass("d-none");
      $("li[data-table=my-species]").addClass("d-none");
      $('.myproject-rows').addClass('d-none')
      $('.publicproject-rows').removeClass('d-none')
      $('div[data-table=public-page]').removeClass('d-none')
      $('div[data-table=my-page]').addClass('d-none')
    } else {
      $("li[data-table=my-species]").removeClass("d-none");
      $("li[data-table=public-species]").addClass("d-none");
      $('.myproject-rows').removeClass('d-none')
      $('.publicproject-rows').addClass('d-none')
      $('div[data-table=public-page]').addClass('d-none')
      $('div[data-table=my-page]').removeClass('d-none')

    }
  });

  /*
  $("#myproject-tab").on("click", function () {
    $(".my-species").removeClass("d-none");
    $(".public-species").addClass("d-none");
  });*/

  // clickable datatable

  $('.clickable-row').on('click',function(){
    window.location = $(this).data("href");
  })

  // filter data by species
  $("#filterTableBySpecies").on("click", function () {
    let table_id = $(".pj-tab li.now").data('table');
    let list_name;
    if (table_id == "publicproject") {
      list_name = "public-species";
    } else {
      list_name = "my-species";
    }

    //let s = $(`[name=species-filter].${table_id}:checked`).val();

   // if (s != undefined && s != "") {
      // show loading
      //$(".tab-area").addClass("loading");
      // current table
      let check_list = $(`ul.species-check-list li.now:not(.all)[data-table=${list_name}]`);
      let speciesArray = [];
      check_list.each(function () {
        if ($(this).data('species')!=undefined){
          speciesArray.push($(this).data('species'));
        }
      });

      console.log(speciesArray)

/*
      if (speciesArray.length) {
        $.ajax({
          type: "POST",
          url: "/api/update_datatable",
          data: { table_id: table_id, species: speciesArray },
          headers: { "X-CSRFToken": $csrf_token },
          success: function (response) {
            $(".tab-area").removeClass("loading");
            // reset table
            $("#" + table_id + "-table")
              .DataTable()
              .destroy();
            $("#" + table_id + "-tbody").html("");
            let i;
            for (i = 0; i < response.length; i++) {
              // keyword & funding agency
              if ((response[i][2] == "None") | (response[i][2] == null)) {
                response[i][2] = "";
              }

              if ((response[i][4] == "None") | (response[i][2] == null)) {
                response[i][4] = "";
              }

              $("#" + table_id + "-tbody").append(`
                              <tr class='clickable-row' data-href="info/${response[i][0]}/">
                                  <td>${response[i][0]}</td>
                                  <td>${response[i][1]}</td>
                                  <td>${response[i][2]}</td>
                                  <td>${response[i][3]}</td>
                                  <td>${response[i][4]}</td>
                                  <td>${response[i][5]}</td>
                                  <td>${response[i][6]}</td>
                                  <td>${response[i][7]}</td>
                              </tr>`);
            }
            $("#" + table_id + "-table").DataTable({ language: language_settings, columnDefs: column_defs, order: [[3, "desc"]] });
          },
        });
      }
      */



   // } else {
   //   resetTable();
   // }
  });
});
/*

// datatable
let language_settings = {
  decimal: "",
  emptyTable: "查無資料",
	info: "正在檢視第 _START_ 至 _END_ 筆，總共 _TOTAL_ 筆",
  infoEmpty: "共 0 筆",
  infoFiltered: "",
  infoPostFix: "",
  thousands: ",",
  lengthMenu: "每頁顯示 _MENU_ 筆",
  loadingRecords: "載入中...",
  processing: "處理中...",
  search: "查詢🔍",
  zeroRecords: "查無符合資料",
  paginate: {
    next: `下一頁 <svg xmlns="http://www.w3.org/2000/svg" width="9.187" height="17.053" viewBox="0 0 9.187 17.053">
    <g id="next" transform="translate(-102.297 0)">
      <g id="Group_17" data-name="Group 17" transform="translate(102.297 0)">
        <path id="Path_59" data-name="Path 59" d="M111.291,8.059,103.417.185a.656.656,0,0,0-.928.928L109.9,8.523l-7.411,7.411a.656.656,0,0,0,.928.928l7.874-7.874A.656.656,0,0,0,111.291,8.059Z" transform="translate(-102.297 0)" fill="#529a81"/>
      </g>
    </g>
  </svg>`,
    previous: `<svg xmlns="http://www.w3.org/2000/svg" width="9.187" height="17.053" viewBox="0 0 9.187 17.053">
    <g id="pre" transform="translate(111.483 17.054) rotate(180)">
      <g id="Group_17" data-name="Group 17" transform="translate(102.297 0)">
        <path id="Path_59" data-name="Path 59" d="M111.291,8.059,103.417.185a.656.656,0,0,0-.928.928L109.9,8.523l-7.411,7.411a.656.656,0,0,0,.928.928l7.874-7.874A.656.656,0,0,0,111.291,8.059Z" transform="translate(-102.297 0)" fill="#529a81"/>
      </g>
    </g>
  </svg> 上一頁`,
  },
};

let column_defs = [
  { visible: false, targets: 0 },
  { width: "33%", targets: 1 },
  { width: "12%", targets: 2 },
  { width: "10%", targets: 3 },
  { width: "15%", targets: 4 },
  { width: "10%", targets: 5 },
  { width: "10%", targets: 6 },
  { width: "10%", targets: 7 },
];

let myproject_table = $("#myproject-table").DataTable({
  dom: "<'row'<'col-6'B>><'row' tr>" +
  "<'page-inf' <'leftbox' i <'input-item' l>>>" +
  "<'page-num' p>",
  language: language_settings,
  columnDefs: column_defs,
  fixedColumns: true,
  order: [[1, "asc"]],
});


$('#myproject-table_wrapper').addClass('d-none')

let publicproject_table = $("#publicproject-table").DataTable({
  language: language_settings,
  columnDefs: column_defs,
  fixedColumns: true,
  order: [[1, "asc"]],
  serverSide: true,

  ajax: {
    type: "POST",
    dataType: 'json',
    url: "/api/project/overview",
    headers: { 'X-CSRFToken': $csrf_token },
    data: function (d) {
      d.times = window.conditions.times;
      d.pk = pk;
      d.species = window.conditions.species;
      d.sa = window.conditions.sa;
      d.start_date = window.conditions.start_date;
      d.end_date = window.conditions.end_date;
      d.start_altitude = window.conditions.start_altitude;
      d.end_altitude = window.conditions.end_altitude;
      d.deployment = window.conditions.deployment;
      d.folder_name = window.conditions.folder_name;
      d.county_name = window.conditions.county_name;
      d.protectarea_name = window.conditions.protectarea_name;
      d.orderby = $('.orderby svg.sort-icon-active').data('orderby');
      d.sort = $('.orderby svg.sort-icon-active').data('sort');
    },
    error: function () {
      $('.dataTables_processing').hide()
      alert('未知錯誤，請聯繫管理員');
    }
  },
});*/


// radio style
/*
$("input[type=radio]").click(function () {
  let group = $(this).attr("name");
  let table_id = $(".col-10 .active").attr("aria-controls");
  $(`input[name=${group}].${table_id}`).parent("label").children("svg").remove();
  $('<i class="fas fa-check title-dark w-12"></i>').insertBefore(this);
});*/

// reset table

$('#resetTable').on('click',function(){
    resetTable()
})

function resetTable() {
  $("#myproject-table").DataTable().destroy();
  $("#publicproject-table").DataTable().destroy();

  $("#myproject-tbody").html($myproject);

  $("#publicproject-tbody").html($publicproject);

  $("#myproject-table").DataTable({
    language: language_settings,
    columnDefs: column_defs,
    fixedColumns: true,
    order: [[1, "asc"]],
  });



  $("#publicproject-table").DataTable({
    language: language_settings,
    columnDefs: column_defs,
    fixedColumns: true,
    order: [[1, "asc"]],
  });

 // $('.dataTables_length label').addClass('input-item')

  // filter

  /*
  let table_id = $(".col-10 .active").attr("aria-controls");
  if (table_id == "myproject") {
    $(".my-species").removeClass("d-none");
    $(".public-species").addClass("d-none");
  } else {
    $(".my-species").addClass("d-none");
    $(".public-species").removeClass("d-none");
  }*/

  let table_id = $(".pj-tab li.now").data('table');
  if (table_id == 'publicproject'){
    $("li[data-table=public-species]").removeClass("d-none");
    $("li[data-table=my-species]").addClass("d-none");
  } else {
    $("li[data-table=my-species]").removeClass("d-none");
    $("li[data-table=public-species]").addClass("d-none");
  }

  // reset checkbox
  $('.species-check-list li').removeClass('now').addClass('now')

  //$("input[name=species-filter][type=checkbox]").prop("checked", false);
  //$("input[type=checkbox].all").prop("checked", true);

  // radio
  //$(".fa-check").remove();
  //$('<i class="fas fa-check title-dark"></i>').insertBefore($("input[type=radio].all"));
}