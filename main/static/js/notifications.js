import * as notify_api from './'

function create_notification(message, color, title, time){
    notification = new Notification({
        title: title,
        background: color,
        text: message
    })
    notification.send();
}




