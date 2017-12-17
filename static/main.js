function displayStatus(statusObj){ // Push the object data to the div's on the website
    currentState = statusObj;
    
    if (statusObj['currTemp']!=null){
        $('#currTemp').text(statusObj['currTemp'].toFixed(2));
    }
    
    if (statusObj['desiredTemp']!=null){
        $('#desiredTemp').text(statusObj['desiredTemp'].toFixed(1));
    }

    if(statusObj['forceCH']==0){
        $('#ForceCH').attr("class", "btn btn-lg btn-primary")
    } else if(statusObj['forceCH']>0) {
        $('#ForceCH').attr("class", "btn btn-lg btn-danger")
    }

    if(statusObj['forceHW']==0){
        $('#ForceHW').attr("class", "btn btn-lg btn-primary")
    } else if(statusObj['forceHW']>0) {
        $('#ForceHW').attr("class", "btn btn-lg btn-danger")
    }

    if(statusObj['holidayMode']==0){
        $('#HolidayMode').attr("class", "btn btn-lg btn-primary")
    } else if(statusObj['holidayMode']==1) {
        $('#HolidayMode').attr("class", "btn btn-lg btn-danger")
    }

    if(statusObj['weekendMode']==0){
        $('#WeekendMode').attr("class", "btn btn-lg btn-primary")
    } else if (statusObj['weekendMode']==1){
        $('#WeekendMode').attr("class", "btn btn-lg btn-danger")
    }

    if(statusObj['summerMode']==0){
        $('#SummerMode').attr("class", "btn btn-lg btn-primary")
    } else if (statusObj['summerMode']==1) {
        $('#SummerMode').attr("class", "btn btn-lg btn-danger")
    }

    if(statusObj['chStatus']==1){
        $('#chOff').hide();
        $('#chOn').show();
    } else {
        $('#chOff').show();
        $('#chOn').hide();
    }

    if(statusObj['hwStatus']==1){
        $('#hwOff').hide();
        $('#hwOn').show();
    } else {
        $('#hwOff').show();
        $('#hwOn').hide();
    }    
}

function sendAJAX(command){ //
    $.ajax({
        url:"/robot/api/"+command,
        type: "PUT",
        contentType:"application/json",
        dataType:"json",
        success: function(data) {
                console.log(data);
                displayStatus(data);
        }
    });
}


$(function() { //document ready

    $("#ForceCH").click( function(e) {
        e.preventDefault();
        sendAJAX('ForceCH');
    });

    $("#ForceHW").click( function(e) {
        e.preventDefault();
        sendAJAX('ForceHW');
    });

    $("#TempPlus").click( function(e) {
        e.preventDefault();
        sendAJAX('TempPlus');
    });

    $("#TempMinus").click( function(e) {
        e.preventDefault();
        sendAJAX('TempMinus');
    });

    $("#SummerMode").click( function(e) {
        e.preventDefault();
        sendAJAX('SummerMode');
    });

    $("#HolidayMode").click( function(e) {
        e.preventDefault();
        sendAJAX('HolidayMode');
    });

    $("#WeekendMode").click( function(e) {
        e.preventDefault();
        sendAJAX('WeekendMode');
    });

    window.setInterval(function(){
        sendAJAX('getStatus');
}, 2000);


sendAJAX('status');
}); //end of document ready




