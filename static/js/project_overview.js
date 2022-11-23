var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $publicproject = $('#publicproject-tbody').html()
var $myproject = $('#myproject-tbody').html()

$(function () {
  // species: if other checkbox checked, uncheck 'all'
  $("input[name='species-filter'].filter:not(.all)").click(function () {
    let table_id = $(".col-10 .active").attr("aria-controls");
    if ($(this).is(":checked")) {
      $('<i class="fas fa-check title-dark w-12"></i>').insertBefore($(this));
    } else {
      $(this).parent("label").children("svg").remove();
    }
    $(`input[name='species-filter'].all.${table_id}`).prop("checked", false);
    $(`#species-list-all-${table_id} label`).children("svg").remove();
  });

  // species: if 'all' checked, check all checkbox
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
  });

  // speices filter list
  $("#publicproject-tab").on("click", function () {
    $(".public-species").removeClass("d-none");
    $(".my-species").addClass("d-none");
  });

  $("#myproject-tab").on("click", function () {
    $(".my-species").removeClass("d-none");
    $(".public-species").addClass("d-none");
  });

  // clickable datatable
  $("#myproject-table").on("click", ".clickable-row", function () {
    window.location = $(this).data("href");
  });

  $("#publicproject-table").on("click", ".clickable-row", function () {
    window.location = $(this).data("href");
  });

  // filter data by species
  $(".select").on("click", function () {
    let table_id = $(".col-10 .active").attr("aria-controls");
    let s = $(`[name=species-filter].${table_id}:checked`).val();
    if (s != undefined && s != "") {
      // show loading
      $(".tab-area").addClass("loading");
      // current table
      let check_list = $(`[name=species-filter].${table_id}:checked`);
      let speciesArray = [];
      check_list.each(function () {
        speciesArray.push($(this).val());
      });
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
    } else {
      resetTable();
    }
  });
});

// datatable
let language_settings = {
  decimal: "",
  emptyTable: "查無資料",
  info: "共 _TOTAL_ 筆",
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
    next: "下一頁",
    previous: "上一頁",
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
  language: language_settings,
  columnDefs: column_defs,
  fixedColumns: true,
  order: [[1, "asc"]],
});

let publicproject_table = $("#publicproject-table").DataTable({
  language: language_settings,
  columnDefs: column_defs,
  fixedColumns: true,
  order: [[1, "asc"]],
});

// radio style
$("input[type=radio]").click(function () {
  let group = $(this).attr("name");
  let table_id = $(".col-10 .active").attr("aria-controls");
  $(`input[name=${group}].${table_id}`).parent("label").children("svg").remove();
  $('<i class="fas fa-check title-dark w-12"></i>').insertBefore(this);
});

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

  // filter
  let table_id = $(".col-10 .active").attr("aria-controls");
  if (table_id == "myproject") {
    $(".my-species").removeClass("d-none");
    $(".public-species").addClass("d-none");
  } else {
    $(".my-species").addClass("d-none");
    $(".public-species").removeClass("d-none");
  }

  // reset checkbox
  //$("input[name=species-filter][type=checkbox]").prop("checked", false);
  //$("input[type=checkbox].all").prop("checked", true);

  // radio
  //$(".fa-check").remove();
  //$('<i class="fas fa-check title-dark"></i>').insertBefore($("input[type=radio].all"));
}