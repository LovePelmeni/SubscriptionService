function process_subscription_creation(data){
    var url = new URL("http://localhost:8000/create/subscription");
    var request = new XMLHttpRequest();
    request.open('POST', url, false);
    request.send(data);
}

$("#createSubscriptionForm").addEventListener('submit', function(event){
    $.ajax({
        url: validate_url,
        type: 'POST',
        data: $(this).serialize(),
        success: function(response){
           var data = $(this).serialize();
           return process_subscription_creation(data);
        },
        error: function(error){
            console.log('Exception has occurred. ', error);
        }
    })
});