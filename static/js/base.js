$(document).ready(function () {
    $("li.active").removeClass("active");
    $('a[href="' + location.pathname + '"]')
    .closest(".nav-link")
    .addClass("active");
});

function updateIsRead(){
    $.ajax({
    url: "{% url 'update_is_read' %}",
    type: 'GET',
    success: function(){
        $('.has-unread').hide()
    }
    });
}

// tooltip
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

function getAuth() {
    let url = "https://orcid.org/oauth/authorize?client_id=APP-F6POVPAP5L1JOUN1&response_type=code&scope=/authenticate&redirect_uri=" + location.protocol + "//" + location.host + "/callback/orcid/auth?next={{ request.path }}";
    window.location.href = url;
}
