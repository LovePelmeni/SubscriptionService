import typing

from Analytic.main.urls import urlpatterns
from rest_framework import views

from django.contrib.sessions.models import Session
import django.core.serializers.json

import django.core.mail, logging
from django.conf import settings
from rest_framework import status

from Analytic.main.signals import subscription_delete

logger = logging.getLogger(__name__)

class ConfirmEmailVerificationController(views.APIView):

    def process_subscription_delete(self, subscription_id: typing.Union[str, int]):
        subscription_delete.send(subscription_id=subscription_id)

    @csrf.requires_csrf_token
    def post(self, request):
        try:
            format = '' # / * deserialize verify token format.
            subscription_id = request.query_params.get('subscription_id')
            session = models.Session.objects.get(
            id=request.query_params.get('session_id')).get_decoded()
            if not session['subscription_id'] == \
            django.core.serializers.deserialize(format,
            request.query_params.get('verification_code')):
                return django.http.HttpResponse(status=400)

            self.process_subscription_delete(subscription_id)
            return django.http.HttpResponse(status=status.HTTP_200_OK)

        except(django.core.serializers.json.DeserializationError,) as exception:
            logger.error('Invalid Verification Token could not deserialize. Exception: %s' % exception)
            return django.http.HttpResponse(status=400)


urlpatterns += path('confirm/delete/subscription/', ConfirmEmailVerificationController.as_view())
class ConfirmEmailVerification(object):

    def __call__(self, *args, **kwargs):
        self.confirm(**kwargs)

    def confirm(self, verification_code: str, subscription_id: str,
    username: str, email: str, session_id: str, subscription_name: str):

        link = 'http://' + settings.APPLICATION_HOST + ':%s'\
        % settings.APPLICATION.PORT + reverse('main:confirmation') \
        + "?subscription_id=%s&verification_code=%s&session_id=%s" % (
            subscription_id, verification_code, session_id
        )
        message = "Hello, %s. You Can verify to delete your Subscription '%s' at %s" % (
        username, subscription_name, link)
        self.send_email(to_email=email, from_email=settings.MANAGEMENT_EMAIL, message=message)

    def send_email(self, to_email: str, from_email: str,  message):
        try:
            email = django.core.mail.EmailMessage(
            to=to_email,
            from_email=from_email,
            body=message)
            email.fail_silently = False
            email.send()
        except(django.core.mail.BadHeaderError,) as exception:
            logger.error('Could not send email: exception: %s' % exception)



