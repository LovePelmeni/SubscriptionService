from __future__ import annotations
import django.dispatch.dispatcher
from . import models
import logging

logger = logging.getLogger(__name__)

add_purchaser = django.dispatch.dispatcher.Signal()
remove_purchaser = django.dispatch.dispatcher.Signal()
user_deleted = django.dispatch.dispatcher.Signal()
subscription_delete = django.dispatch.dispatcher.Signal()


@django.dispatch.dispatcher.receiver(user_deleted)
def handle_tasks_on_user_deletion(sender, user_id, **kwargs):
    import django_celery_beat.models as celery_models
    celery_models.PeriodicTask.objects.filter( # better to implement raw sql query instead of the deletion loop.
    enabled=True, name__startswith='Subscription-%s' % user_id).raw('DELETE FROM main_subscription')
    logger.debug('All Subscriptions for user with ID -%s has been cleaned up.' % user_id)


@django.dispatch.dispatcher.receiver(remove_purchaser)
def remove_user_from_purchasers(sender, purchaser_id, subscription_id, **kwargs):
    try:
        purchaser = models.APICustomer.objects.get(id=purchaser_id)
        models.Subscription.objects.get(
        id=subscription_id).purchasers.remove(purchaser)
        logger.debug('user has been removed...')

    except(django.core.exceptions.ObjectDoesNotExist, AttributeError):
        logger.debug('user does not exist.')

@django.dispatch.dispatcher.receiver(add_purchaser)
def add_user_to_purchasers(sender, purchaser_id, subscription_id, **kwargs):
    try:
        purchaser = models.APICustomer.objects.get(id=purchaser_id)
        models.Subscription.objects.get(
        id=subscription_id).purchasers.add(purchaser)
        logger.debug('user has been added.')

    except(django.core.exceptions.ObjectDoesNotExist, AttributeError):
        logger.debug('user does not exist..')


import asgiref.sync
async def send_deleted_info_emails(emails: typing.List[str]):
    """/ * Sends emails to all the users """
    pass

@django.dispatch.dispatcher.receiver(signal=subscription_delete)
def process_subscription_delete(subscription_id: typing.Union[str | int]):
    pass


