import * as notify_api from ".notifications.js"

function notify_window(message, title, time){
   notify_api.create_notification(message, title, time);
   console.log('notification has been created..');
}

function disactivate_subscription(sub_id){

    var customer_id = document.getElementById('customer_id').value;
    var url = new URL("http://localhost:8000/disactivate/subscription/");
    url.searchParams.append('sub_id', sub_id, 'customer_id', customer_id);
    $.ajax({
        url: url,
        async: false,
        type: "POST",
        success: function(response){
            console.log('subscription has been disactivated..');
        },
        error: function(error){
            console.log('subscription has responded with exception, ', error);
        }
    });
}

$('#disactivate_subscription').addEventListener('submit', function(event){
    event.preventDefault();
    var sub_id = $(this).subscription_id.value;
    disactivate_subscription(sub_id);
});




