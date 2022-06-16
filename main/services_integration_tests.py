from django.test import TestCase
from django.test.runner import DiscoverRunner

from django.conf import settings
from django.db import connections
import socket

from django.conf import settings
import requests.exceptions
import pika.exceptions


class MongoIntegrationTestCase(TestCase):

    def test_connection_established(self):
        try:
            connection = socket.create_connection((settings.MONGO_DATABASE_HOST,
            int(settings.MONGO_DATABASE_PORT)))
            connection.close()
        except(socket.timeout):
            msg = 'Mongo Database Does Not Responding...'
            raise socket.timeout(msg)


class RabbitmqExternalIntegrationTestCase(TestCase):

    def test_connection_established(self):
        try:
            channel = pika.BlockingConnection(
            parameters=pika.ConnectionParameters(
            host=settings.RABBITMQ_BROKER_HOST, port=settings.RABBITMQ_BROKER_PORT,
            virtual_host=settings.RABBITMQ_BROKER_VHOST,
            credentials=pika.PlainCredentials(settings.RABBITMQ_BROKER_USER, settings.RABBITMQ_BROKER_PASSWORD)))
            channel.close()
        except(requests.exceptions.RequestException,) as exception:
            msg = 'Rabbitmq External Server Does Not Responding...'
            raise exception(msg)

        except(pika.exceptions.AMQPConnectionError,) as exception:
            raise exception


class PostgresSQLIntegrationTestCase(TestCase):

    def test_connection_established(self):
        try:
            connection = socket.create_connection(
            address=(settings.POSTGRES_HOST, settings.POSTGRES_PORT), timeout=10)
            connection.close()
        except(socket.timeout):
            msg = 'PostgresSQL Database Does Not Responding...'
            raise socket.timeout(msg)


