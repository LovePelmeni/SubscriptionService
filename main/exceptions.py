import django.http
from rest_framework import status


class ExpiredSubscription(BaseException):
    pass

class MongoDatabaseIsNotRunning(BaseException):
    pass

class InvalidSubscriptionPayload(BaseException):
    pass