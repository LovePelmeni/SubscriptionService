import typing
from django import forms
from rest_framework import serializers
from . import models
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_duration
import datetime, django.core.exceptions
import logging

logger = logging.getLogger(__name__)


class SubFormSerializer(forms.ModelForm):

    subscription_name = serializers.CharField(label='Subscription Name', required=True)
    owner_id = serializers.IntegerField(label='owner_id', required=True)
    amount = serializers.IntegerField(label='amount', required=True)
    currency = serializers.CharField(label='Currency', required=True)

    class Meta:
        model = models.Subscription
        fields = ('subscription_name', 'owner_id', 'amount', 'currency')

    def validate_currency(self, value: str):
        if not value in ('usd', 'rub', 'eu'):
            raise django.core.exceptions.ValidationError
        return value

    def validate_owner_id(self, value):
        return django.core.exceptions.ValidationError if not value in \
        models.APICustomer.objects.values_list('id', flat=True) else value


class SubCatalogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Subscription
        exclude = ('created_at', 'owner_id')

from django.utils.translation import gettext_lazy as _

class ActivateSubSerializer(serializers.Serializer):

    subscription_name = serializers.CharField(label=_('Required Field'))
    subscription_id = serializers.IntegerField(label=_('Required Field'))

    purchaser_id = serializers.IntegerField(label=_('Required Field'))
    owner_id = serializers.IntegerField(label=_('Required Field'))

    amount = serializers.IntegerField(label=_('Required Field'))
    currency = serializers.ChoiceField(choices=choices, label=_("Required Field"))



