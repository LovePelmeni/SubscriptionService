import os
import celery.exceptions

import django.conf.urls
import redis

from django.test import TestCase, TransactionTestCase

from rest_framework import status
from django.test.utils import override_settings

import logging, pika, pika.exceptions
from .models import APICustomer, Subscription
from .sub_tasks import *
import json

from django_celery_beat import models as celery_models
from .celery_register import celery_module as celery_application


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

    def test_get_applied_subscription_list(self):
        response = self.client.get('http://localhost:8076/get/purchased/subs/?customer_id=%s' % self.customer_id)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


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