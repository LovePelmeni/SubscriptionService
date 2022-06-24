from django import forms
from . import models
import django.core.exceptions
import datetime

class ExpirePeriodField(forms.DurationField):

    def __init__(self, **kwargs):
        super(ExpirePeriodField, self).__init__(**kwargs)

    def prepare_expire_string(self, value: datetime.timedelta):
        string = '{:02d}:{:02d}:{:02d}'.format(value.seconds // 3600, value.seconds // 60, value.seconds)
        if value.days is not None:
            string = '%s ' % (value.days) + string
        return string

    def prepare_value(self, value):
        if not isinstance(value, datetime.timedelta):
            self.prepare_expire_string(value)
        return value

    def validate(self, value):
        return super().validate(value)


choices = [
    ('usd', 'usd'),
    ('eu', 'eu'),
    ('rub', 'rub')
]


class ActivateSubForm(forms.Form):

    subscription_name = forms.CharField()
    subscription_id = forms.IntegerField()

    purchaser_id = forms.IntegerField()
    owner_id = forms.IntegerField()

    amount = forms.IntegerField()
    currency = forms.ChoiceField(choices=choices)


class SubscriptionForm(forms.ModelForm):

    name = forms.CharField(label='Subscription Name', widget=forms.TextInput, required=True)
    amount = forms.DecimalField(label='Price', required=True)
    currency = forms.CharField(label='Currency', required=True)

    class Meta:
        model = models.Subscription
        fields = ('name', 'amount', 'currency')

    def validate_currency(self, value):
        if not value in ('usd', 'eu', 'rub'):
            raise django.core.exceptions.ValidationError
        return value




