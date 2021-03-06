import logging
import typing

import celery.exceptions
from django.db import models

from django_celery_beat import models as celery_models
import datetime, django.utils.timezone
import django.db.models.functions, time

from . import mongo_api
from django.views.decorators.cache import cache_page

import logging
from django.utils.translation import gettext_lazy as _



logger = logging.getLogger(__name__)

class APICustomer(models.Model):  # represents the Main App Custom User Model, but locally in this application.

    objects = models.Manager()
    username = models.CharField(verbose_name=_('Username'), null=False, max_length=100)
    email = models.EmailField(verbose_name=_("Email Address"), null=False, max_length=100, default="-")
    balance = models.IntegerField(verbose_name=_('User Balance'), null=False, default=0)
    created_at = models.DateField(verbose_name=_('Created At'), default=django.utils.timezone.now())

    class Meta:
        verbose_name = 'API Sub Customer'
        verbose_name_plural = 'API Sub Customers'

    def get_username(self):
        return self.username

    def get_balance(self):
        return self.balance

    def delete(self, using=None, **kwargs):
        return super().delete(using=using, **kwargs)

    def has_sub_permission(self, sub_id):
        return int(sub_id) in self.purchased_subs.values_list('id', flat=True)

currency_choices = [
    ('usd', 'usd'),
    ('eu', 'eu'),
    ('rub', 'rub')
]

#SUBSCRIPTION_ATTRIBUTES:


class Subscription(models.Model):

    objects = models.Manager()
    subscription_name = models.CharField(verbose_name=_('Name'), max_length=100)

    owner_id = models.IntegerField(verbose_name=_('Owner Id'), null=False)
    amount = models.IntegerField(verbose_name=_('Amount'), max_length=100)
    currency = models.CharField(verbose_name=_('Currency'), choices=currency_choices, max_length=20, null=False, default='usd')

    created_at = models.DateField(verbose_name=_('Expire Period'), auto_now_add=True, max_length=100, null=True)
    purchasers = models.ManyToManyField(verbose_name=_('Purchasers'), to=APICustomer, related_name='purchased_subs', null=True)


    def __str__(self):
        return self.subscription_name

    class Meta:
        verbose_name = 'Subscription'



