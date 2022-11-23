  $(function () {

    $.ajax({
      url: "/api/get_growth_data",
      success: function (data) {
        // plot
        data_growth_year = [];
        data.data_growth_image.forEach((i) => data_growth_year.push(i[0]));

        data_growth_image_count = [];
        data.data_growth_image.forEach((i) => data_growth_image_count.push(i[1] / 10000));

        data_growth_deployment_count = [];
        data.data_growth_deployment.forEach((i) => data_growth_deployment_count.push(i[1]));

        // plot - data_growth
        Highcharts.chart("data_growth", {
          chart: {
            marginTop: 40,
            backgroundColor: null,
          },
          exporting: { enabled: false },
          credits: { enabled: false },
          title: { text: "" },
          xAxis: [
            {
              categories: data_growth_year,
              crosshair: true,
            },
          ],
          legend: {
            itemStyle: {
              fontSize: "14px",
              fontWeight: "regular",
            },
          },
          yAxis: [
            {
              // Primary yAxis
              allowDecimals: false,
              labels: {
                format: "{value}",
                style: {
                  fontSize: "14px",
                },
              },
              title: {
                align: "high",
                offset: 0,
                text: "相機位置數",
                rotation: 0,
                y: -20,
                x: -10,
                style: {
                  fontSize: "14px",
                },
              },
              opposite: true,
            },
            {
              // Secondary yAxis
              allowDecimals: false,
              gridLineWidth: 0,
              title: {
                align: "high",
                offset: 0,
                text: "影像累積筆數(萬)",
                rotation: 0,
                y: -20,
                x: 30,
                style: {
                  fontSize: "14px",
                },
              },
              labels: {
                format: "{value}",
                style: {
                  fontSize: "14px",
                },
              },
            },
          ],
          tooltip: {
            shared: true,
          },
          series: [
            {
              name: "影像累積筆數(萬)",
              type: "column",
              yAxis: 1,
              data: data_growth_image_count,
              tooltip: {},
              color: "#AECC82",
            },
            {
              name: "相機位置數",
              type: "spline",
              data: data_growth_deployment_count,
              tooltip: {},
              marker: {
                lineWidth: 2,
                lineColor: "#AECC82",
                fillColor: "white",
              },
              color: "#AECC82",
              label: {
                enabled: false,
              },
            },
          ],
          responsive: {
            rules: [
              {
                condition: {
                  maxWidth: 500,
                },
                chartOptions: {
                  legend: {
                    floating: false,
                    layout: "horizontal",
                    align: "center",
                    verticalAlign: "bottom",
                    x: 0,
                    y: 0,
                  },
                  yAxis: [
                    {
                      labels: {
                        align: "right",
                        x: 0,
                        y: -6,
                      },
                      showLastLabel: false,
                    },
                    {
                      labels: {
                        align: "left",
                        x: 0,
                        y: -6,
                      },
                      showLastLabel: false,
                    },
                    {
                      visible: false,
                    },
                  ],
                },
              },
            ],
          },
        });
      },
    });

    $.ajax({
      url: "/api/get_species_data",
      success: function (data) {
        // plot - species

        species_data_name = [];
        data.species_data.forEach((i) => species_data_name.push(i[1]));
        species_data_count = [];
        data.species_data.forEach((i) => species_data_count.push(i[0] / 10000));
        Highcharts.chart("species_data", {
          chart: {
            type: "bar",
            marginTop: 40,
            backgroundColor: null,
          },
          exporting: { enabled: false },
          credits: { enabled: false },
          title: { text: "" },
          xAxis: {
            categories: species_data_name,
            tickInterval: 1,
            title: {
              text: null,
              style: {
                fontSize: "14px",
              },
            },
            labels: {
              step: 1,
              style: {
                fontSize: "14px",
              },
            },
          },
          yAxis: {
            allowDecimals: false,
            min: 0,
            title: {
              text: "資料累積筆數(萬)",
              align: "high",
              style: {
                fontSize: "14px",
              },
            },
            labels: {
              overflow: "justify",
              style: {
                fontSize: "14px",
              },
            },
          },
          tooltip: {
            pointFormatter: function () {
              var string = this.series.name + ": " + this.y + "<br>";
              return string;
            },
          },
          series: [
            {
              name: "資料累積筆數(萬)",
              data: species_data_count,
              color: "#AECC82",
            },
          ],
          legend: {
            itemStyle: {
              fontSize: "14px",
              fontWeight: "regular",
            },
          },
        });
      },
    });
  });

  // map
  
  const StudyAreaIcon = L.icon({
    iconUrl: '/static/icon/marker-icon-error.png',
    iconSize: [33, 60],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [33, 60],
    shadowAnchor: [31, 77],
    className: "myStudyAreaIcon",
  });
  
  const StudyAreaIconSelect = L.icon({
    iconUrl: '/static/icon/marker-icon-error-select.png',
    iconSize: [33, 60],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [33, 60],
    shadowAnchor: [31, 77],
    className: "myStudyAreaIcon",
  });


  const DeploymentIcon = L.icon({
    iconUrl: '/static/icon/marker-icon.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
    shadowAnchor: [31, 77],
    className: "myDeploymentIcon",
  });
  
  const DeploymentIconSelect = L.icon({
    iconUrl: '/static/icon/marker-icon-select@2x.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
    shadowAnchor: [31, 77],
    className: "myDeploymentIcon",
  });
  


  let map = L.map("map", {tap: false}).setView([23.5, 121.2], 7);
  L.tileLayer("https://{s}.tile.osm.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  function onEachFeature(feature, layer) {
        layer.on({
            mouseover: e => {
                e.target.setStyle({
                    fillColor: 'green',
                });
            },
            mouseout: e => {
                e.target.setStyle({
                    fillColor: '#7C9C2D',
                });
            },
            click: e => {
              $('#map-info').removeClass('d-none');
              $('#default-info').addClass('d-none');
                let county = e.target.feature.properties.COUNTYNAME;
                $('#click-county').html(county);
                countyOnClick(county);
            },
            
        })
    }


  function countyOnClick(county){
    $.ajax({
      url: '/api/stat_county',
      data: {"county": county},
      dataType: "json",
      success: function(response) {
        //map.removeLayer(marker);
        $('.myStudyAreaIcon').remove();

        response.studyarea.forEach(
          (i) =>
            (marker = new L.marker([i[1], i[0]], { icon: StudyAreaIcon })
              .bindPopup(
                `${i[3]}<small>${i[2]}</small>`
              )
              .on("mouseover", function (e) {
                this.openPopup();
                e.target.setIcon(StudyAreaIconSelect);                                 
              })
              .on("mouseout", function (e) {
                this.closePopup();
                e.target.setIcon(StudyAreaIcon);                                   
              })
              .on("click", function (e) {
                $('#map-info').html('<div class="loader"></div>');
                $.ajax({
                  url: '/api/stat_studyarea',
                  data: {"said": i[4]},
                  dataType: "json",
                  success: function(response) {
                    // 返回鍵
                    $('.map-explore').html(`<a class="link" onClick="resetMapExplore('${county}')">返回</a>`)
                    // 更換右側統計圖
                    $('#map-info').html(`
                      <h1 id="click-county" class="title-light mb-3">${i[3]}</h1>
                      <h4 class="mb-3 county-title" >${i[2]}</h4>
                      <div id="deployment_data" class="mx-auto"></div>
                      <img class="d-sa-icon " src='/static/icon/marker-icon.png'> 相機位置
                    `);
                    Highcharts.chart("deployment_data", {
                      chart: {
                        type: "column",
                        marginTop: 40,
                        backgroundColor: null,
                      },
                      exporting: { enabled: false },
                      credits: { enabled: false },
                      title: { text: "" },
                      xAxis: {
                        categories: response.name,
                        tickInterval: 1,
                        title: {
                          text: "相機位置",
                          style: {
                            fontSize: "14px",
                          },
                        },
                        labels: {
                          style: {
                            fontSize: "14px",
                          },
                        },
                      },
                      yAxis: {
                        allowDecimals: false,
                        min: 0,
                        title: {
                          align: "high",
                          offset: 0,
                          text: "影像累積筆數",
                          rotation: 0,
                          y: -20,
                          style: {
                            fontSize: "14px",
                          },                        
                        },
                        labels: {
                          format: "{value}",
                          overflow: "justify",
                          style: {
                            fontSize: "14px",
                          },
                        },
                      },
                      tooltip: {
                        pointFormatter: function () {
                          var string = this.series.name + "：" + this.y + "<br>";
                          return string;
                        },
                      },
                      series: [
                        {
                          name: "影像累積筆數",
                          data: response.count,
                          color: "#AECC82",
                        },
                      ],
                      legend:{ enabled:false },
                    });
                    // 更換左側地圖
                    // 重設縮放 & 移除其他icon
                    map.setView([response.center[1], response.center[0]], 10);
                    $('.myStudyAreaIcon').remove();
                    $('.countyPoly').addClass('d-none');
                    response.deployment_points.forEach(
                      (r) =>
                        (marker = new L.marker([r[2], r[1]], { icon: DeploymentIcon })
                          .on("mouseover", function (e) {
                            e.target.setIcon(DeploymentIconSelect);                                 
                          })
                          .on("mouseout", function (e) {
                            e.target.setIcon(DeploymentIcon);                                     
                          })                        
                          .bindTooltip(r[3], { permanent: true, direction: 'top' })
                          .addTo(map)));
                  }})
              })
              .addTo(map))
        );

        $('#map-info').html(
          `<h1 id="click-county" class="title-light mb-3">${county}</h1>
          <div class="row desp">
            <div class="col-3 text-left">
              計畫總數
            </div>
            <div class="col-9 text-left">
              ${response.num_project}
            </div>
          </div>
          <div class="row desp">
            <div class="col-3 text-left">
              相機位置
            </div>
            <div class="col-9 text-left">
              ${response.num_deployment}
            </div>
          </div>
          <div class="row desp">
            <div class="col-3 text-left">
              總辨識進度
            </div>
            <div class="col-9 text-left">
              ${response.identified} %
            </div>
          </div>
          <div class="row desp">
            <div class="col-3 text-left">
              總相片數
            </div>
            <div class="col-9 text-left">
              ${response.num_image}
            </div>
          </div>
          <div class="row desp">
            <div class="col-3 text-left">
              相機總工時
            </div>
            <div class="col-9 text-left">
              ${response.num_working_hour}
            </div>
          </div>
          <div class="row desp">
            <div class="col-3 text-left">
              出現物種
            </div>
            <div class="col-9 text-left">
              ${response.species}
            </div>
          </div>
          <img class="d-sa-icon" src='/static/icon/marker-icon-error.png'> 樣區
          `
        )
      }
  })
  }

  function polystyle(feature) {
    return {
      fillColor: "#7C9C2D",
      weight: 1.2,
      color: "white",
      className: "countyPoly",
    };
  }

  $.getJSON("/static/map/twCounty2010.geo.json", function (ret) {
    L.geoJSON(ret, {onEachFeature: onEachFeature, style: polystyle}).addTo(map);
    //L.geoJSON(ret, { style: polystyle }).addTo(map);
  });

    function resetMapExplore(county){
      $('.myDeploymentIcon').remove();
      $('.leaflet-tooltip').remove();
      map.setView([23.5, 121.2], 7);
      $('.countyPoly').removeClass('d-none');
      // trigger event
      countyOnClick(county);
    
    }
  