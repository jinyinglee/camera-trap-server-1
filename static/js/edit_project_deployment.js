var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');

    // preselect geo
    // $('#').selectpicker('val', ""); 
$( function() {
    

    let pk = $('input[name=pk]').val();
    $.ajax({
      type: 'GET',
      url: `/api/get_edit_info/?pk=${pk}&type=deployment`,
      success: function (response) {
        for (let i = 0; i < response.study_area.length; i++) {
            if (response.study_area[i].parent_id != null){
                $(`#collapse_${ response.study_area[i].parent_id }`).prepend(`<li>
                <div class="studyarea-click" data-parent="${ response.study_area[i].parent_id }" id="${ response.study_area[i].id }" 
                    data-said="${ response.study_area[i].id }" data-saname="${ response.study_area[i].name }">
                    <div class="studyarea-name d-inline-block">${ response.study_area[i].name }
                    </div>
                </div>
            </li>`);
            $('.studyarea-click').on('click',function(){
                let id = $(this).data('said');
                let sa_name = $(this).data('saname');
                getDep(id, sa_name)
            })
            $(`#collapse_${ response.study_area[i].parent_id }`).removeClass('d-none');
            
            } 
            /*else {
                $(`#collapse_${ response.study_area[i].id }`).remove()
            }*/
        }
        },
    })

    $('#goBack').on('click',function(){
        window.history.back();
    })

    $('#addSa').on('click',function(){
        let name = $('#addStudyArea').val();
        name_list = []
        $('#studyarea-list div.studyarea-name').each(function(){
            name_list.push($(this).text());
        });
        if (name=='' ){
            $('#addStudyArea-feedback').html('樣區名稱為必填');
            $('#addStudyArea').addClass("is-invalid").addClass("was-validated");
        } else if (name_list.includes(name)){
            $('#addStudyArea-feedback').html('樣區名稱不得重複');
            $('#addStudyArea').addClass("is-invalid").addClass("was-validated");
        } else {
            $.ajax({
                type: 'POST',
                url: "/api/add_studyarea",
                data: {'name': name, 'project_id': $('input[name=pk]').val()},
                headers:{"X-CSRFToken": $crf_token},
                success: function (response) {
                    let new_id = response.study_area_id;
                    $('#addStudyArea-li').before(`
                                        <li>
                                            <div class="studyarea-click studyarea-name d-inline-block" id="${new_id}" 
                                            data-said="${new_id}" data-saname="${name}"
                                            data-bs-toggle="collapse" href="#collapse_${new_id}" role="button" 
                                            aria-expanded="false" aria-controls="collapse_">
                                                <div class="studyarea-name d-inline-block">${name}</div>
                                            </div>
                                        </li>
                                        <div class="collapse" id="collapse_${new_id}">
                                            <!-- 新增子樣區 -->
                                            <!--
                                            <li>
                                                <input id="collapse_${new_id}_add" class="border-0 shadow-none form-control bg-light w-90" type="text" placeholder=" + 新增子樣區"> 
                                            </li>
                                            -->
                                        </div>`) 
                    $('.studyarea-click').on('click',function(){
                        let id = $(this).data('said');
                        let sa_name = $(this).data('saname');
                        getDep(id, sa_name)
                    })
                    $('#addStudyArea').val('');
                    $('#addSaModal').modal('hide');
                },
                error: function (response) {
                    alert('未知錯誤，請聯繫管理員')
                }
            })
        }
    
    })
    

    $('#addDeployment').on('click',async function(){
        // vegetation = []
        var vegetation = await getVegetationItem().then(result => vegetation = result)
        
        var protectedarea = await getProtectedareaItem().then(result => protectedarea = result)

        var county =await  getCountyItem().then(result => county = result)
        
        //目前的id到哪
        let new_id = parseInt($('input[name=deprecated]').last().val()) + 1;
        $('#deployment').append(`<tr class="new-row">
                                    <td>
                                        <input type="hidden" name="id">
                                        <input type="text" name="name" class="form-control"></td>
                                    <td><input type="text" name="longitude" class="form-control"></td>
                                    <td><input type="text" name="latitude" class="form-control"></td>
                                    <td><input type="text" name="altitude" value="" class="form-control"></td>
                                    <td><select name="county" class="selectpicker form-control" 
                                    data-live-search-placeholder="搜索" data-live-search="true">
                                    ${county}
                                    </select></td>
                                    <td><select name="protectedarea" class="selectpicker form-control" 
                                    data-live-search-placeholder="搜索" data-live-search="true">
                                    ${protectedarea}
                                    </select></td>
                                    <td><select name="vegetation" class="selectpicker form-control" 
                                    data-live-search-placeholder="搜索" data-live-search="true">
                                    ${vegetation}
                                    </select></td>
                                    
                                    <td><input type="text" name="landcover" class="form-control"></td>
                                    <td><input type="checkbox" name="deprecated" value="${new_id}"></td>
                                    <td><a class="removeButton btn bg-white text-gray">x</a></td>
                                </tr>`)
            $('select').selectpicker();
    })
    

    $('#addDepolymentSubmit').on('click',function(){
            // check required fields
    // name
    let name = $('#deployment [name="name"]')

    name_list = []
    name.each(function(){
        name_list.push($(this).val());
    });

    name.each(function(){
        if ($(this).val()==''){
            $(this).addClass("is-invalid").addClass("was-validated");
        } else if (name_list.includes($(this).val())){
            let count = 0;
            for(let i = 0; i < name_list.length; ++i){
                if(name_list[i] == $(this).val())
                    count++;
            }
            if (count > 1){
                $(this).addClass("is-invalid").addClass("was-validated");
            } else {
                $(this).removeClass("is-invalid").removeClass("was-validated");
            }
        } else {
            $(this).removeClass("is-invalid").removeClass("was-validated");
        }            
    });

    let longitude = $('#deployment [name="longitude"]')
    longitude.each(function(){
        let value = $(this).val()
        if (!$.isNumeric(value)){
            $(this).addClass("is-invalid").addClass("was-validated");
        } else {
            $(this).removeClass("is-invalid").removeClass("was-validated");
        }            
    });

    let latitude = $('#deployment [name="latitude"]')
    latitude.each(function(){
        let value = $(this).val()
        if (!$.isNumeric(value)){
            $(this).addClass("is-invalid").addClass("was-validated");
        } else {
            $(this).removeClass("is-invalid").removeClass("was-validated");
        }            
    });

    // altitude
    let altitude = $('#deployment [name="altitude"]')
    altitude.each(function(){  
        let value = $(this).val()
        if (value==''){
            //pass
        } else {
            if (!$.isNumeric(value)){
                $(this).addClass("is-invalid").addClass("was-validated");
            } else {
                $(this).removeClass("is-invalid").removeClass("was-validated");
            }
        }
    });

    // show invalid feedback

    // submit
    if(!$('#deploymentForm .is-invalid').length){

        names = []
        name.each(function(){
            names.push($(this).val());
        });

        latitudes = []
        latitude.each(function(){
            latitudes.push($(this).val());
        });

        longitudes = []
        longitude.each(function(){
            longitudes.push($(this).val());
        });

        altitudes = []
        altitude.each(function(){
            altitudes.push($(this).val());
        });

        counties = []
        $('#deployment [name="county"]').each(function(){
            counties.push($(this).val());
        });
        // county.each(func
        protectedareas = []
        $('#deployment [name="protectedarea"]').each(function(){
            protectedareas.push($(this).val());
        });
        
        landcovers = []
        $('#deployment [name="landcover"]').each(function(){
            landcovers.push($(this).val());
        });

        vegetations = []
        $('#deployment [name="vegetation"]').each(function(){
            vegetations.push($(this).val());
        });

        did = []
        $('#deployment [name="id"]').each(function(){
            did.push($(this).val());
        });

        deprecated = []
        $('input[name="deprecated"]:checked').each(function(){
            deprecated.push($(this).val());
        });

        $.ajax({
        type: 'POST',
        url: "/api/add_deployment",
        data: {'project_id': $('input[name=pk]').val(),
               'study_area_id': $('.current_sa').attr('id'),
               'geodetic_datum': $('select').val(),
               'names': names,
               'longitudes': longitudes,
               'latitudes': latitudes,
               'altitudes': altitudes,
               'counties': counties,
               'protectedareas': protectedareas,
               'landcovers' : landcovers,
               'vegetations': vegetations,
               'did': did,
               'deprecated': deprecated},
        headers:{"X-CSRFToken": $crf_token},
        success: async function (response) {
            // 如果有新增的話，要把新增的deployment_id寫回去
            // 改成remove沒有did的 然後新增回去
            console.log(response)
            $('.new-row').remove();
            var vegetation = await getVegetationItem().then(result => vegetation = result)
        
            var protectedarea = await getProtectedareaItem().then(result => protectedarea = result)
            
            var county = await getCountyItem().then(result => county = result)

            for (let i = 0; i < response.length; i++) {
                // 如果是null顯示空值
                for (j = 0; j < 9; j++ ){
                    if ((response[i][j] == null)|(response[i][j] == 'null')){
                        response[i][j] = ""}
                }
                let d_checked
                if (response[i][11]==true){
                    d_checked='checked';
                }
                let protectedarea_a = [];
                    for (let j = 0; j < protectedarea.length; j++) {
                        if (response[i][6]){
                            a = protectedarea[j].toString().replace(response[i][6], response[i][6]+' selected')
                            protectedarea_a.push(a)
                        }else{
                            protectedarea_a.push(protectedarea[j].toString())
                        }
                    }
                    
                    let vegetation_a = [];
                    for (let j = 0; j < vegetation.length; j++) {
                        if (response[i][7]){
                            a = vegetation[j].toString().replace(response[i][7], response[i][7]+' selected')
                            vegetation_a.push(a)
                        }else{
                            vegetation_a.push(vegetation[j].toString())
                        }
                    }
                    let county_a = [];
                    for (let j = 0; j < county.length; j++) {
                        if (response[i][5]){
                            a = county[j].toString().replace(response[i][5], response[i][5]+' selected')
                            county_a.push(a)
                        }else{
                            county_a.push(county[j].toString())
                        }
                    }

                await $('#deployment').append(`
                <tr>
                    <td>
                        <input type="hidden" name="id" value="${response[i][0]}">
                        <input type="text" name="name" class="form-control text-truncate" value="${response[i][1]}">
                    </td>
                    <td><input type="text" name="longitude" class="form-control" value="${response[i][2]}"></td>
                    <td><input type="text" name="latitude" class="form-control" value="${response[i][3]}"></td>
                    <td><input type="text" name="altitude" class="form-control" value="${response[i][4]}"></td>
                    <td><select name="county" class="selectpicker form-control" 
                    data-live-search-placeholder="搜索" data-live-search="true">${county_a}</select></td>
                    <td><select name="protectedarea" class="selectpicker form-control" 
                    data-live-search-placeholder="搜索" data-live-search="true">${protectedarea_a}</select></td>
                    <td><select name="vegetation" class="selectpicker form-control" 
                    data-live-search-placeholder="搜索" data-live-search="true">${vegetation_a}</select></td>
                    <td><input type="text" name="landcover" class="form-control" value="${response[i][8]}"></td>
                    <td><input type="checkbox" name="deprecated" value="${i}" ${d_checked}></td>
                    <td><a class="removeButton btn bg-white text-gray" data-did="${response[i][0]}">x</a></td>
                </tr>`)
            }
            $('select').selectpicker();
         
            alert('設定已儲存');
        },
        error: function (response) {
            alert('未知錯誤，請聯繫管理員');
        }
    })
    
    } else {
        alert('請檢查輸入欄位是否正確，且相機位置名稱不得重複');
    }


    })


})


function addDepolymentSubmit(){
}



function getDep(id,sa_name){
        // clear previous select
        $('#deployment').html('')
        $('#studyarea-list .title-dark').removeClass("title-dark").removeClass('current_sa');
        $('#deployment-list').removeClass("d-none");
        $('#initial-content').addClass("d-none");
        $('.sa-name').html(sa_name);
    
        let selector = '#' + id
        $(selector).addClass("title-dark").addClass('current_sa')

        //判斷選項
        vegetation = []
        var vegetation =  getVegetationItem().then(result => vegetation = result)

        protectedarea = []
        var protectedarea =  getProtectedareaItem().then(result => protectedarea = result)

        county = []
        var county =  getCountyItem().then(result => county = result)
        

        // deployment    
        // ajax here
        $.ajax({
            type: 'POST',
            url: "/api/deployment/",
            data: {'study_area_id': id},
            headers:{"X-CSRFToken": $crf_token},
            success: function (response) {
                //let data = JSON.parse(response.replace(/'/g, '"'))
                for (let i = 0; i < response.length; i++) {
                    // 如果是null顯示空值
                    for (j = 0; j < 7; j++ ){
                        if ((response[i][j] == null)|(response[i][j] == 'null')){
                            response[i][j] = ""}
                    }
                    let d_checked
                    if (response[i][11]==true){
                        d_checked='checked';
                    }

                    let protectedarea_a = [];
                    for (let j = 0; j < protectedarea.length; j++) {
                        if (response[i][6]){
                            a = protectedarea[j].toString().replace(response[i][6], response[i][6]+' selected')
                            protectedarea_a.push(a)
                        }else{
                            protectedarea_a.push(protectedarea[j].toString())
                        }
                    }
                    
                    let vegetation_a = [];
                    for (let j = 0; j < vegetation.length; j++) {
                        if (response[i][7]){
                            a = vegetation[j].toString().replace(response[i][7], response[i][7]+' selected')
                            vegetation_a.push(a)
                        }else{
                            vegetation_a.push(vegetation[j].toString())
                        }
                    }
                    let county_a = [];
                    for (let j = 0; j < county.length; j++) {
                        if (response[i][5]){
                            a = county[j].toString().replace(response[i][5], response[i][5]+' selected')
                            county_a.push(a)
                        }else{
                            county_a.push(county[j].toString())
                        }
                    }
                    $('#deployment').append(`
                    <tr>
                        <td>
                            <input type="hidden" name="id" value="${response[i][0]}">
                            <input type="text" name="name" class="form-control text-truncate" value="${response[i][1]}">
                        </td>
                        <td><input type="text" name="longitude" class="form-control" value="${response[i][2]}"></td>
                        <td><input type="text" name="latitude" class="form-control" value="${response[i][3]}"></td>
                        <td><input type="text" name="altitude" class="form-control" value="${response[i][4]}"></td>
                        <td><select name="county" class="selectpicker form-control" 
                        data-live-search-placeholder="搜索" data-live-search="true">${county_a}</select></td>
                        <td><select name="protectedarea" class="selectpicker form-control" data-live-search-placeholder="搜索" data-live-search="true">${protectedarea_a}</select></td>
                        <td><select name="vegetation" class="selectpicker form-control"data-live-search-placeholder="搜索" data-live-search="true">${vegetation_a}</select></td>
                        <td><input type="text" name="landcover" class="form-control" value="${response[i][8]}"></td>
                        <td><input type="checkbox" name="deprecated" value="${i}" ${d_checked}></td>
                        <td><a class="removeButton btn bg-white text-gray" data-did="${response[i][0]}">x</a></td>
                    </tr>`)
                }
                $('select').selectpicker();
            },
            error: function (response) {
            }
        })


}

$('.studyarea-click').on('click',function(){
    let id = $(this).data('said');
    let sa_name = $(this).data('saname');
    getDep(id, sa_name)
})


function selectStudyArea(id, sa_name){
    
}

function getVegetationItem(){
    return new Promise((resolve, reject) => {
        obj2 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'vegetation'},
            headers:{"X-CSRFToken": $crf_token},
            async:false,
            success: function (data) {
                obj2.push(`<option value=''}></option>`)
                for (let i = 0; i < data.length; i++) {
                    obj2.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve (obj2)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}
function getCountyItem(){
    return new Promise((resolve, reject) => {
        obj4 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'county'},
            headers:{"X-CSRFToken": $crf_token},
            async:false,
            success: function (data) {
                obj4.push(`<option value=''}></option>`)
                for (let i = 0; i < data.length; i++) {
                    obj4.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve (obj4)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}
function getProtectedareaItem(){
    return new Promise((resolve, reject) => {
        obj3 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'protectedarea'},
            headers:{"X-CSRFToken": $crf_token},
            async:false,
            success: function (data) {
                obj3.push(`<option value=''}></option>`)
                for (let i = 0; i < data.length; i++) {
                    obj3.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve(obj3)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}



function addDeployment(){
}



$("#deployment-table").on("click", ".removeButton", function(event) {
    let row = $(this).closest("tr");
    if ($(this).data('did')==undefined){
    // 如果是新增的相機位置 -> 直接刪除
        row.remove();
    } else {
    // 如果是已存在的相機位置 -> 後端刪除
        $.ajax({
            type: 'GET',
            url: "/delete_dep_sa",
            data: {'type': 'dep', 'id': $(this).data('did'), 'project_id': $('input[name=pk]').val()},
            success: function (response) {
                if (response.status=='exists'){
                    alert('欲刪除的相機位置下尚有影像，請先刪除影像或將影像搬移至其他相機位置')
                } else if (response.status=='done') {
                    alert('已成功刪除')
                    row.remove();
                }
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })
    }
});



$('#addSaModal').on('hidden.bs.modal', function() { 
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
    $('#addStudyArea').val('');
});


$('#editSaModal').on('shown.bs.modal', function() { 
    $('#editStudyArea').val($('.current_sa .studyarea-name').html());
    $('#editStudyArea-id').val($('.current_sa').attr('id'));
});

$('#editSaModal').on('hidden.bs.modal', function() { 
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
});


$('#editSa_edit').on('click',function(){
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
    let name = $('#editStudyArea').val();
    // 也有可能是sub
    let original_name = $('.current_sa .studyarea-name').html();
    name_list = []
    $('#studyarea-list div.studyarea-name').each(function(){
        if ($(this).text() != original_name){
        name_list.push($(this).text())
        }
    });
    if (name=='' ){
        $('#editStudyArea-feedback').html('樣區名稱為必填');
        $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
    } else if (name_list.includes(name)){
        $('#editStudyArea-feedback').html('樣區名稱不得重複');
        $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
    } else {
        
        $.ajax({
            type: 'GET',
            url: "/edit_sa",
            data: {'name': name, 'id': $('#editStudyArea-id').val()},
            success: function (response) {
                // 修改左側列表名稱
                $('.current_sa .studyarea-name').html(name)
                // 修改右側大標
                $('.sa-name').html(name)
                $('#editSaModal').modal('hide');
                alert('設定已儲存')
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員')
            }
        })
        
    }    
})




$('#editSa_delete').on('click',function(){
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
        // delete
        $.ajax({
            type: 'GET',
            url: "/delete_dep_sa",
            data: {'type': 'sa', 'id': $('#editStudyArea-id').val(), 'project_id': $('input[name=pk]').val()},
            success: function (response) {
                if (response.status=='exists'){
                    alert('欲刪除的樣區下尚有影像，請先刪除影像或將影像搬移至其他樣區')
                } else if (response.status=='done') {
                    alert('已成功刪除')
                    $('.current_sa').parent().next('.collapse').remove()
                    $('.current_sa').parent('li').remove()
                    $('#editSaModal').modal('hide')
                    // 右側恢復起始
                    $('#initial-content').removeClass("d-none");
                    $('#deployment-list').addClass("d-none");
                }
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })

})


/*
function editSa(type){

    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");

    if (type=='edit'){
        let name = $('#editStudyArea').val();
        // 也有可能是sub
        let original_name = $('.current_sa .studyarea-name').html();
        name_list = []
        $('#studyarea-list div.studyarea-name').each(function(){
            if ($(this).text() != original_name){
            name_list.push($(this).text())
            }
        });
        if (name=='' ){
            $('#editStudyArea-feedback').html('樣區名稱為必填');
            $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
        } else if (name_list.includes(name)){
            $('#editStudyArea-feedback').html('樣區名稱不得重複');
            $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
        } else {
            
            $.ajax({
                type: 'GET',
                url: "/edit_sa",
                data: {'name': name, 'id': $('#editStudyArea-id').val()},
                success: function (response) {
                    // 修改左側列表名稱
                    $('.current_sa .studyarea-name').html(name)
                    // 修改右側大標
                    $('.sa-name').html(name)
                    $('#editSaModal').modal('hide');
                    alert('設定已儲存')
                },
                error: function (response) {
                    alert('未知錯誤，請聯繫管理員')
                }
            })
            
        }    
    } else {
        // delete
        $.ajax({
            type: 'GET',
            url: "/delete_dep_sa",
            data: {'type': 'sa', 'id': $('#editStudyArea-id').val(), 'project_id': $('input[name=pk]').val()},
            success: function (response) {
                if (response.status=='exists'){
                    alert('欲刪除的樣區下尚有影像，請先刪除影像或將影像搬移至其他樣區')
                } else if (response.status=='done') {
                    alert('已成功刪除')
                    $('.current_sa').parent().next('.collapse').remove()
                    $('.current_sa').parent('li').remove()
                    $('#editSaModal').modal('hide')
                    // 右側恢復起始
                    $('#initial-content').removeClass("d-none");
                    $('#deployment-list').addClass("d-none");
                }
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })
    }
    
}
*/



function addSa(){
}
