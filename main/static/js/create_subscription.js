import * as notify_api from "./notifications.js"


function process_subscription_creation(data){

    var customer_id = document.getElementById('customer_id').value;
    var url = new URL("http://localhost:8000/create/subscription");
    var request = new XMLHttpRequest();
    var profileURL = new URL("http://localhost:8000/get/custom/subs/?customer_id=" + customer_id);

    request.open('POST', url, false);
    request.send(data);

    if (request.response_code in (200, 201)){
        var message = 'New Subscription Has been Created Successfully. Go Check it out: ' + profileURL;
        var title = 'Success'
    } else {
        var title = 'Failed'
        var message = 'Failed to create new subscription.'
    }
    notify_api.create_notification(message, title, null);
}

$("#createSubscriptionForm").addEventListener('submit', function(event){
    $.ajax({
        url: validate_url,
        type: 'POST',
        data: $(this).serialize(),
        success: function(response){
            console.log('success responded...');
           var data = $(this).serialize();
           return process_subscription_creation(data);
        },
        error: function(error){
            console.log('Exception has occurred. ', error);
        }
    })
});