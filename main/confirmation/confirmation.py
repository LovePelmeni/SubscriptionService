import typing
from rest_framework import views

from django.contrib.sessions.models import Session
import django.core.serializers.json, django.contrib.sessions.backends.db
import django.utils.decorators

import django.core.mail, logging
from django.conf import settings

from rest_framework import status
from django.views.decorators import csrf

import django.urls
try:
    import signals, models, urls
except(ImportError, ModuleNotFoundError,):
    from main import signals, models, urls

logger = logging.getLogger(__name__)

class ConfirmEmailVerificationController(views.APIView):

    def process_subscription_delete(self, subscription_id: typing.Union[str, int]):
        signals.subscription_delete.send(sender=self, subscription_id=subscription_id)

    @django.utils.decorators.method_decorator(decorator=csrf.requires_csrf_token)
    def post(self, request):
        try:
            session = django.contrib.sessions.backends.db.SessionStore(
            session_key=request.query_params.get('session_id'))
            subscription_id = session.get('subscription_id')

            if not subscription_id or not subscription_id in models.Subscription.objects.values_list('id', flat=True):
                return django.http.HttpResponse(status=400)

            self.process_subscription_delete(subscription_id)
            return django.http.HttpResponse(status=status.HTTP_200_OK)

        except(KeyError, django.contrib.sessions.models.Session.DoesNotExist,) as exception:
            logger.error('Seems like '
            'Session has no key "subscription_id" or That Request Session does not exist.'
            'Exception: %s' % exception)
            return django.http.HttpResponse(status=404)


confirmation_urlpatterns = [

    django.urls.path('confirm/delete/subscription/',
    ConfirmEmailVerificationController.as_view(), name='confirmation-url'),

]

urls.urlpatterns += confirmation_urlpatterns

class ConfirmEmailVerification(object):

    def __init__(self,
    reason: typing.Optional[str],
    subscription_id: typing.Union[str, int],
    username: str,
    session_id: str,
    email: str,
    subscription_name: typing.Optional[str]):

        self.reason = reason
        self.subscription_id = subscription_id
        self.username = username
        self.session_id = session_id
        self.email = email
        self.subscription_name = subscription_name

    def __call__(self, *args, **kwargs):
        self.confirm()

    def confirm(self):

        link = 'http://' + settings.APPLICATION_HOST + ':%s'\
        % settings.APPLICATION.PORT + django.urls.reverse('main:confirmation') \
        + "?session_id=%s" % (self.session_id)
        message = "Hello, %s. You Can verify to delete your Subscription '%s' at %s" % (
        self.username, self.subscription_name if self.subscription_name else '*****', link)
        self.send_email(to_email=self.email, from_email=settings.SUPPORT_EMAIL, message=message)

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


