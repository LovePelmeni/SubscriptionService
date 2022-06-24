import os
import celery.exceptions

import django.conf.urls
import redis, django.middleware.csrf

from django.test import TestCase, TransactionTestCase, Client

from rest_framework import status
from django.test.utils import override_settings

import logging, pika, pika.exceptions
from .models import APICustomer, Subscription
from .sub_tasks import *
import json, pytest

from django_celery_beat import models as celery_models
from .celery_register import celery_module as celery_application

test_client = Client()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestCeleryTaskExecutionCase(TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.idempotency_key = 'some-test-idempotency-key'

        self.purchaser_id = APICustomer.objects.create(username='Customer').id
        self.sub_id = Subscription.objects.create(amount=100, subscription_name='TestSubscription', owner_id=self.purchaser_id).id
        self.task_credentials = {
            'idempotency_key': self.idempotency_key,
            'purchaser_id': self.purchaser_id,
            'subscription_id': self.sub_id,
            'task_name': 'some-test-task-name',
        }

    def tearDown(self) -> None:
        try:
            celery_application.celery_app.control.discard_all()
            return super().tearDown()
        except(celery.exceptions.CeleryError) as exception:
            raise exception

    def test_expire_subscription_task(self):
        try:
            expire_subscription.delay(**self.task_credentials)
            self.assertGreaterEqual(len(celery_application.celery_app.tasks.values()), 1)

        except(celery.exceptions.CeleryError, celery.exceptions.TaskRevokedError) as e:
            raise e

class TestApplySubCase(TransactionTestCase):


    def setUp(self):

        import datetime
        self.owner = APICustomer.objects.create(username='Owner')
        self.sub = Subscription.objects.create(owner_id=self.owner.id, amount=1000, subscription_name='Subscription')
        self.purchaser = APICustomer.objects.create(username='AnotherUser')
        celery_models.IntervalSchedule.objects.create(every='28', period=celery_models.IntervalSchedule.DAYS)

        self.subscription_document_credentials = {}
        self.subscription_credentials = {
            'owner_id': self.owner.id,
            'subscription_name': self.sub.subscription_name,
            'subscription_id': self.sub.id,
            'amount': self.sub.amount,
            'currency': 'usd',
            'purchaser_id': self.purchaser.id,
            'created_at': datetime.datetime.now(),
            'active': True
        }
        self.idempotency_key = 'test-idempotency-key'


    def test_apply_subscription(self):
        response = self.client.post('http://localhost:8076/activate/sub/?customer_id=%s&sub_id=%s' % (self.purchaser.id, self.sub.id),
        data=self.subscription_credentials)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(celery_models.PeriodicTask.objects.all()), 1)


    def tearDown(self):
        try:
            celery_models.PeriodicTask.objects.raw('DELETE FROM django_celery_beat_periodictask')
            return super().tearDown()
        except(django.db.IntegrityError, django.core.exceptions.ObjectDoesNotExist,) as exception:
            raise exception


    def test_unapply_subscription(self):
        response = self.client.delete('http://localhost:8076/disactivate/sub/',
        data={'sub_id': self.sub.id, 'customer_id': self.purchaser.id, 'idempotency_key': self.idempotency_key})
        self.assertIn(response.status_code, (status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
        status.HTTP_404_NOT_FOUND, status.HTTP_200_OK))
        self.assertLess(len(celery_models.PeriodicTask.objects.all()), 1)


class TestObtainAppliedSubsCase(TestCase):

    def setUp(self):
        self.customer_id = APICustomer.objects.create(username='TestCustomer').id
        self.idempotency_key = "test-idempotency-key"

    def test_get_single_subscription(self):
        response = self.client.get('http://localhost:8076/get/purchased/sub/?idempotency_key=%s' % self.customer_id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscription', json.loads(response.content).keys())

    def test_get_applied_subscription_list(self):
        response = self.client.get('http://localhost:8076/get/purchased/subs/?customer_id=%s' % self.customer_id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('queryset', json.loads(response.content).keys())


class TestCatalogSubCase(TestCase):

    def setUp(self):
        self.customer_id = APICustomer.objects.create(username='TestUser', balance=100).id

    def test_get_single_subscription(self):
        response = self.client.get('http://localhost:8076/get/sub/?customer_id=%s' % self.customer_id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_get_subscription_list(self):
        response = self.client.get('http://localhost:8076/get/sub/list/?customer_id=%s' % self.customer_id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


class TestCheckSubPermissionStatusCase(TestCase):

    def create_dependencies(self):
        self.user_id = APICustomer.objects.create(username='TestCustomer').id
        self.sub_id = Subscription.objects.create(owner_id=self.user_id, amount=100, subscription_name='TestSubscription').id
        return self.user_id, self.sub_id

    def setUp(self):
        self.customer_id, self.sub_id = self.create_dependencies()

    def test_check_sub_permissions(self):
        response = self.client.get('http://localhost:8076/check/sub/permission/?customer_id=%s&sub_id=%s'
        % (self.customer_id, self.sub_id,))
        self.assertEquals(response.status_code, status.HTTP_200_OK)


class TestCustomerEventsViaRabbitMQCase(TestCase):

    def setUp(self):
        self.customer_data = {}
        self.customer = APICustomer.objects.create(username='SomeUser')

    def test_send_creation_event(self):

        response = self.client.post('http://localhost:8076/create/customer/', data=self.customer_data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(APICustomer.objects.all()), 2)

    def test_send_deletion_event(self):
        response = self.client.delete('http://localhost:8076/delete/customer/?user_id=%s' % self.customer.id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(APICustomer.objects.all()), 1)



class SubscriptionFailedDelete(Exception):
    pass


class VerificationFailed(Exception):
    pass


import pytest, unittest.mock, requests.exceptions
from . import models


class TestDeleteSubscriptionFunctionalityCase(unittest.TestCase):

    def setUp(self) -> None:
        from . import views
        self.customer_data = {'username': "SomeUser", 'email': 'someeamil@gmail.com'}
        self.customer = models.APICustomer.objects.using(settings.MAIN_DATABASE).create(**self.customer_data)
        self.subscription = models.Subscription.objects.using(settings.MAIN_DATABASE).create(
        owner_id=self.customer.id, amount=1000, currency='eur')

        self.subscription.purchasers.using(settings.MAIN_DATABASE).create(**self.customer_data)
        self.controller = views.DeleteSubscription()


    def mocked_email_confirmation_session(self, fake=False):

        import django.http, django.contrib.sessions.backends.db, datetime # replace the session date
        session = django.contrib.sessions.backends.db.SessionStore()
        session['subscription_id'] = self.subscription.id if not fake else 'invalid-subscription-id'
        session.set_expiry(value=30)
        session.create()
        return session.session_key


    def test_email_verification_endpoint(self):

        from .confirmation import confirmation

        http_session_key = self.mocked_email_confirmation_session(fake=False)
        response = test_client.post(path='http://localhost:8000/confirm/delete/'
        'subscription/?session_id=%s' % http_session_key,
        partimeout=10, headers={'X-CSRF-Token':
        django.middleware.csrf._get_new_csrf_token(), 'Content-Type': 'application/json'})

        self.assertEquals(response.status_code, 200)


    def test_fail_email_verification_endpoint(self):

        with unittest.mock.patch('main.confirmation.confirmation.'
        'ConfirmEmailVerificationController.post') as mocked_controller:

            mocked_controller.side_effect = VerificationFailed
            with self.assertRaises(expected_exception=VerificationFailed):
                response = test_client.post('http://localhost:8000/confirm/delete/subscription/',
                headers={'X-CSRF-Token': django.middleware.csrf._get_new_csrf_token()},
                content_type='application/json')
                self.assertNotEquals(response.status_code, 201)


    def test_fail_delete_subscription(self):
        from .confirmation import confirmation

        with unittest.mock.patch('main.confirmation.confirmation.django.http.HttpResponse') as mocked_request:
            mocked_request.side_effect = requests.exceptions.RequestException
            with self.assertRaises(requests.exceptions.RequestException):

                http_session_key = self.mocked_email_confirmation_session(fake=False)
                response = test_client.post(path='http://localhost:8000/confirm/delete/subscription/',
                params={'session_id': http_session_key}, timeout=10, headers={

                'X-CSRF-Token': django.middleware.csrf._get_new_csrf_token(),
                'Content-Type': 'application/json'})

                self.assertIn(response.status_code, (400, 404))
                mocked_request.assert_called_once()

    def test_process_delete_subscription(self):

        with unittest.mock.patch('main.signals.process_subscription_delete') as mocked_event:
            mocked_event.side_effect = SubscriptionFailedDelete
            with self.assertRaises(SubscriptionFailedDelete):

                signals.process_subscription_delete(subscription_id=self.subscription.id)
                self.assertLess(len(models.Subscription.objects.all()), 1)


class TestSubscriptionDocValidatorCase(unittest.TestCase):

    def setUp(self) -> None:
        from . import models
        self.purchaser = models.APICustomer.objects.create()
        self.owner = models.APICustomer.objects.create()
        self.subscription = models.Subscription.objects.create()

    def mocked_failure_document(self):
        return {'invalid_content': 'invalid_content'}

    def mocked_valid_document(self):
        return {
            'purchaser_id': self.purchaser.id,
            'owner_id': self.owner.id,
            'subscription_id': self.subscription.id,
            'amount': self.subscription.amount,
            'currency': self.subscription.currency,
            'active': True,
            'idempotency_key': None,
            'created_at': datetime.datetime.now(),
            'subscription_task_id': None,
        }

    @unittest.mock.patch('main.sub_api.SubscriptionDocument.validate')
    def test_subscription_validator_succeed(self, mocked_validate_method):

        values = self.mocked_valid_document()
        response = mocked_validate_method(**values)
        mocked_validate_method.assert_called_with(values)
        mocked_validate_method.assert_called_once()
        self.assertIsNotNone(response)

    @unittest.mock.patch('main.sub_api.SubscriptionDocument.validate')
    def test_subscription_validator_fail(self, mocked_validate_method):

        from . import exceptions
        mocked_validate_method.side_effect = exceptions.InvalidSubscriptionPayload
        values = self.mocked_valid_document()

        with self.assertRaises(expected_exception=exceptions.InvalidSubscriptionPayload):
            response = mocked_validate_method(**values)

            mocked_validate_method.assert_called_with(values)
            mocked_validate_method.assert_called_once()
            self.assertIsNone(response)


class TestMongoDBControllersCase(unittest.TestCase):

    def setUp(self) -> None:
        self.purchaser = models.APICustomer.objects.create()

    def mocked_document_content(self):
        return {}

    @unittest.mock.patch('main.mongo_api.upload_new_subscription', autospec=True)
    def test_upload_document(self, mocked_uploader):
        from . import mongo_api
        document = self.mocked_document_content()
        mocked_uploader(document)
        self.assertGreater(len(mongo_api.get_subscription_queryset(
        purchaser_id=self.purchaser_id)), 0)
        mocked_uploader.assert_called_once()
        mocked_uploader.assert_called_with(document)

    @unittest.mock.patch('main.mongo_api.delete_subscription_document', autospec=True)
    def test_delete_document(self, mocked_deletor):
        from . import mongo_api
        subscription = self.mocked_document_content()
        document_id = mongo_api.upload_new_subscription(subscription=subscription)
        mocked_deletor(document_id)
        mocked_deletor.assert_called_once()
        mocked_deletor.assert_called_with(document_id)


    def tearDown(self):
        """Removes all insertions made during the test."""
        from . import mongo_api
        mongo_api.delete_all_subscriptions(self.purchaser.id)