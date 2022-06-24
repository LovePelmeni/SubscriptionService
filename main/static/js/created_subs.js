import * as notify_api from './notifications.js'


function EmailConfirmationDeleteSubscription(sub_id){

    var customer_id = document.getElementById('customer_id').value;
    var url = new URL("http://localhost:8000/delete/subscription/");
    url.searchParams.append('sub_id', sub_id, 'customer_id', customer_id);
    var request = new XMLHttpRequest();
    request.open('DELETE', url, false);
    request.send(null);

    if (!request.status_code in (200, 201)){
        console.log('failed to send email notification, Server responded with. ',
        request.status_code);
    } else {
        var message = 'Confirmation Letter has been sended to you Email.'
        notify_api.create_notification(message, 'Delete Confirmation');
    }
  });
}

$("#DeleteSubscription").addEventListener('submit', function(event){
    event.preventDefault();
    var sub_id = $(this).sub_id;
    EmailConfirmationDeleteSubscription(sub_id);
});

$("#createSubscription").addEventListener('submit', function(event){
    var redirectURL = new URL("http://localhost:8000/create/subscription/");
    return window.location.replace(redirectURL);
});

