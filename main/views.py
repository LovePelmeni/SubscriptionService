import typing, logging, django.core.exceptions, django.http, json

import pika.exceptions
import pymongo.errors

import rest_framework.renderers
from django.views.decorators import cache, csrf

import django.utils.decorators as api_decorators
from django.db import transaction

from . import models, sub_api, mongo_api, permissions
from django_celery_beat import models as celery_models
from django.conf import settings

from rest_framework import \
viewsets, status, views, decorators, response, serializers, generics

from . import permissions, serializers as api_serializers, forms
from django.db import models as lib_models

import django.core.serializers.json, datetime
from bson import json_util
from rest_framework import permissions as rest_perms



logger = logging.getLogger(__name__)


class ObtainAppliedSubscriptionAPIView(viewsets.ViewSet):

    permission_classes = (rest_perms.AllowAny,)

    def handle_exception(self, exc):
        logger.debug('exception has been raised. %s', exc)
        return django.http.HttpResponse(status=status.HTTP_501_NOT_IMPLEMENTED)


    @decorators.action(methods=['get'], detail=False)
    def list(self, request):
        validated_queryset = []
        customer_id = request.query_params.get('customer_id')
        sub_queryset = mongo_api.get_subscription_queryset(purchaser_id=customer_id)

        for subscription in sub_queryset:
            subscription.update({'_id': json_util.dumps(subscription.get('_id'))})
            validated_queryset.append(subscription)

        return django.http.JsonResponse(
        {'queryset': validated_queryset}, status=status.HTTP_200_OK)


    @decorators.action(methods=['get'], detail=False)
    def retrieve(self, request):

        from bson import json_util
        idempotency_key = request.query_params.get('idempotency_key')
        try:
            document = mongo_api.get_subscription_document(key=idempotency_key)
            if '_id' in document.keys():
                document['_id'] = json_util.dumps(document.get('_id'))

            if 'created_at' in document.keys() and isinstance(document.get('created_at'), datetime.datetime):
                document['created_at'] = document.get('created_at').strftime('%H:%d:%m')

        except(AttributeError,):
            return django.http.JsonResponse({'subscription': None})

        logger.debug('document found.')
        return django.http.HttpResponse(status=status.HTTP_200_OK, content=json.dumps({'document': document},
        cls=django.core.serializers.json.DjangoJSONEncoder))


class ObtainCatalogSubscriptionAPIView(viewsets.ModelViewSet):

    serializer_class = api_serializers.SubCatalogSerializer
    permission_classes = (rest_perms.AllowAny,)

    def handle_exception(self, exc):
        logger.debug(msg='%s' % exc)
        if isinstance(exc, django.core.exceptions.ObjectDoesNotExist):
            return django.http.HttpResponseNotFound()

        if isinstance(exc, rest_framework.exceptions.MethodNotAllowed):
            return django.http.HttpResponseNotAllowed(permitted_methods=['get'])

        return django.http.HttpResponse(status=status.HTTP_501_NOT_IMPLEMENTED)


    @decorators.action(methods=['get'], detail=True)
    def retrieve(self, request):
        sub = models.Subscription.objects.filter(id=request.query_params.get('sub_id')).values()
        return django.http.HttpResponse(json.dumps(list(sub),
        cls=django.core.serializers.json.DjangoJSONEncoder), content_type='application/json')


    @decorators.action(methods=['get'], detail=False)
    def list(self, request):
        import requests
        try:
            user_id = request.query_params.get('customer_id')
            user_balance = models.APICustomer.objects.get(id=int(user_id)).get_balance()

            queryset = models.Subscription.objects.annotate(
            is_enough=lib_models.Case(
            lib_models.When(amount__gt=user_balance, then=lib_models.Value('Not Enough Money')),
            lib_models.When(amount__lte=user_balance, then=lib_models.Value('Purchase')),
            default=None, output_field=lib_models.CharField()
            ))
            return django.http.HttpResponse(json.dumps(list(queryset),
            cls=django.core.serializers.json.DjangoJSONEncoder), content_type='application/json')

        except() as exception:
            raise exception

class CustomSubscriptionAPIView(viewsets.ModelViewSet):

    validate_form_class = api_serializers.SubFormSerializer
    queryset = models.Subscription.objects.all()
    permission_classes = (rest_perms.AllowAny,)

    def handle_exception(self, exc):

        if isinstance(exc, django.core.exceptions.ValidationError):
            return django.http.HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        if exc.__class__.__name__ in (django.core.exceptions.ObjectDoesNotExist,
        AttributeError, KeyError):
            return django.http.HttpResponseNotFound()
        return django.http.HttpResponse(status=status.HTTP_501_NOT_IMPLEMENTED)


    @decorators.action(methods=['get'], detail=False)
    def subscription_form(self, request):
        return django.template.response.TemplateResponse(request,
        'main/create_subscription.html', context={'form': forms.SubscriptionForm()})


    @django.utils.decorators.method_decorator(decorator=csrf.requires_csrf_token)
    @transaction.atomic
    def create(self, request, **kwargs) -> django.http.HttpResponse:
        try:
            subscription = self.validate_form_class(request.data)
            if subscription.is_valid():
                models.Subscription.objects.create(**subscription.cleaned_data)
                logger.debug('new sub has been created...')
                return django.http.HttpResponse(status=status.HTTP_200_OK)

            raise django.core.exceptions.ValidationError(message='Invalid Form')
        except() as exception:
            raise exception


    @decorators.action(methods=['get'], detail=True)
    def retrieve(self, request, *args, **kwargs):
        try:
            customer = models.APICustomer.objects.get(id=request.query_params.get('customer_id'))
            subscription = customer.subscriptions.filter(
            id=request.query_params.get('subscription_id')).first()

            return django.http.HttpResponse(status=status.HTTP_200_OK,
            content=json.dumps({'subscription': subscription},
            cls=django.core.serializers.json.DjangoJSONEncoder))

        except(django.core.exceptions.ObjectDoesNotExist, AttributeError) as exception:
            raise exception


    @decorators.action(methods=['get'], detail=False)
    def list(self, request, *args, **kwargs):

        from django.db import models as db_models
        try:
            customer = models.APICustomer.objects.get(id=request.query_params.get('customer_id'))
            queryset = list(customer.subscriptions.annotate(
            purchasers_count=db_models.Count(db_models.F('subscriptions'))).values())
            return django.http.HttpResponse(status=status.HTTP_200_OK,
            content=json.dumps({"queryset": queryset},
            cls=django.core.serializers.json.DjangoJSONEncoder))

        except(django.core.exceptions.ObjectDoesNotExist, AttributeError, KeyError,
        django.db.utils.IntegrityError) as exception:
            raise exception


class CheckSubPermissionStatus(views.APIView):

    permission_classes = (rest_perms.AllowAny,)
    @django.utils.decorators.method_decorator(decorator=cache.never_cache)
    def get(self, request):
        try:
            sub_property = models.APICustomer.objects.get(
            id=request.query_params.get('customer_id')).has_sub_permission(
            sub_id=request.query_params.get('sub_id'))

            return django.http.HttpResponse(status=200, content=json.dumps(
            {'has_property': sub_property}), content_type='application/json')

        except(django.core.exceptions.ObjectDoesNotExist,):
            return django.http.HttpResponseNotFound()


from rest_framework import decorators
class ApplySubscriptionAPIView(viewsets.ViewSet):

    """
    Applying subscription for the Main Application Private Access.

    document:
        sub_id,
        owner,
        purchaser,
        created_at,
        amount,
        approved,
    """
    permission_classes = (
        permissions.IsNotSubscriptionOwner,
        permissions.HasAlreadySubscription,
    )

    server_exceptions = (pymongo.errors.ServerSelectionTimeoutError,
    pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError,)

    def handle_exception(self, exc):

        if exc.__class__ in self.server_exceptions:
            return django.http.HttpResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if isinstance(exc, django.core.exceptions.ValidationError):
            return django.http.HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        if isinstance(exc, django.core.exceptions.PermissionDenied):
            return django.http.HttpResponse(status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

        if isinstance(exc, django.core.exceptions.ObjectDoesNotExist):
            return django.http.HttpResponseNotFound()

        if isinstance(exc, django.db.IntegrityError):
            return django.http.HttpResponse(status=status.HTTP_501_NOT_IMPLEMENTED)

        return django.http.HttpResponseServerError()

    @decorators.action(methods=['get'], detail='Retrieves form for Activating Subscription.')
    def activation_form(self, request):
        from . import forms
        return django.template.TemplateResponse(request, 'main/activate_subscription.html',
        context={'form': forms.ActivateSubForm()})


    @decorators.action(methods=['delete'], detail='Disactivates Subscription.')
    @transaction.atomic
    def destroy(self, request) -> django.http.HttpResponse:
        try:
            idempotency_key = request.query_params.get('idempotency_key')
            sub_api.unapply_subscription(idempotency_key=idempotency_key)
            return django.http.HttpResponse(status=status.HTTP_200_OK)

        except(django.core.exceptions.ObjectDoesNotExist,):
            return django.http.HttpResponseNotFound()


    @decorators.action(methods=['post'], detail='Activates Subscription.')
    @transaction.atomic
    def create(self, request) -> django.http.HttpResponse:
        try:
            from . import forms
            purchaser_id = request.data.get('purchaser_id')
            subscription_id = request.data.get('subscription_id')

            activate_sub_form = forms.ActivateSubForm(request.data)

            if activate_sub_form.is_valid():
                document = sub_api.SubscriptionDocument(**activate_sub_form.cleaned_data,
                created_at=datetime.datetime.now(), approved=True, active=True)

                try:
                    subscription_task_id = sub_api.apply_subscription(

                        document=document,
                        idempotency_key=getattr(document, 'idempotency_key'),
                        purchaser_id=purchaser_id,
                        subscription_id=subscription_id
                    )
                    document.subscription_task_id = subscription_task_id
                    mongo_api.upload_new_subscription(subscription=document)
                    logger.debug('subscription activated.')

                    return django.http.HttpResponse(status=status.HTTP_201_CREATED, content=json.dumps(
                    {'idempotency_key': document.idempotency_key}))

                except(django.core.exceptions.ObjectDoesNotExist, django.db.IntegrityError,) as exception:
                    logger.error('Not Found -%s' % exception)
                    raise exception

            return django.http.HttpResponseBadRequest()

        except() as exception:
            transaction.rollback()
            raise exception

import uuid

class DeleteSubscription(views.APIView):
    """
    / * Responding for Delete Subscription Process.
    """

    response_message: typing.Optional[typing.Union[str, dict]] = {'status_code': 200,
    'message': 'Verification Sent'}

    def check_permissions(self, request):
        customer = models.APICustomer.objects.get(
        id=request.query_params.get('customer_id'))
        return customer.has_sub_permission(sub_id=request.query_params.get('sub_id'))

    def handle_exception(self, exc):
        if isinstance(exc, NotImplementedError):
            return django.http.HttpResponseServerError()
        return django.http.HttpResponseServerError()


    def prepare_error_message(self, code: typing.Optional[int], message: typing.Optional[str]):
        return {'message': 'success' if not message else message, 'code': 200 if not code else code}


    @cache.cache_control(private=True)
    def post(self, request):
        try:
            from .confirmation import confirmation
            subscription_id = request.query_params.get('subscription_id')
            customer = models.APICustomer.objects.get(id=request.query_params.get('customer_id'))

            if customer.email and customer.email != '-':
                email_verification = confirmation.ConfirmEmailVerification(reason=request.data.get('reason'),
                email=customer.email,
                session_id=request.session.key,
                subscription_id=subscription_id,
                username=customer.username,
                subscription_name=None)

                request.session.update({'delete_session_credentials': {'verification_code': verification_code,
                'subscription_id': subscription_id}})
                email_verification.confirm()
            else:
                self.response_message = self.prepare_response_message(code=422, message='Your Email Is Empty.')
            return django.http.HttpResponse(status=self.response_message.get('status_code'),
            content=json.dumps(self.response_message))

        except(django.core.exceptions.ObjectDoesNotExist, django.db.utils.IntegrityError,
        AttributeError, TypeError, KeyError) as exception:
            logger.error('Exception: %s at DeleteSubscription Controller.' % exception)
            raise NotImplementedError





