from celery import shared_task
import django.core.exceptions, django.utils.timezone
from . import mongo_api, signals

from .celery_register import celery_module
from django_celery_beat import models as celery_models
import logging, json, datetime, pymongo.errors

from django.db import transaction
from django.conf import settings



logger = logging.getLogger(__name__)

subscription_schedule, _ = celery_models.IntervalSchedule.objects.get_or_create(every=28,
defaults={'every': '28', 'period': celery_models.IntervalSchedule.DAYS})


@celery_module.celery_app.task
def expire_subscription(purchaser_id,  subscription_id, idempotency_key, task_id=None, **kwargs):
    try:
        document = mongo_api.get_subscription_document(idempotency_key)
        delete_subscription_task(task_id=document.get('subscription_task_id'))
        mongo_api.mark_as_inactive(idempotency_key=idempotency_key)

        signals.remove_purchaser.send(sender=expire_subscription, purchaser_id=purchaser_id,
        subscription_id=subscription_id)
        logger.debug('subscription has been expired.')

    except(NotImplementedError,):
        logger.info('Could not delete subscription object from Mongo DB')

    except(django.core.exceptions.ObjectDoesNotExist,):
        logger.info('Periodic Task Does Not Exist.')
        raise django.core.exceptions.ObjectDoesNotExist

    except(pymongo.errors.AutoReconnect, ) as reconnect_exception:
        logger.error('[RECONNECT EXCEPTION] %s' % reconnect_exception)
        raise reconnect_exception


celery_module.celery_app.tasks.register(expire_subscription) # registering task.


def delete_subscription_task(task_id):
    try:
        celery_models.PeriodicTask.objects.get(id=task_id).delete()
        logger.debug('periodic task has been deleted.')
    except(django.core.exceptions.ObjectDoesNotExist,) as exception:
        raise exception


@transaction.atomic
def create_subscription_task(document, idempotency_key, subscription_id, purchaser_id):
    try:
        celery_task = celery_models.PeriodicTask.objects.create(
            name="Subscription-%s-%s-%s" % (document.purchaser_id, document.amount, document.created_at),
            interval=subscription_schedule,
            one_off=True,
            start_time=datetime.datetime.utcnow() + datetime.timedelta(days=27),

            task="main.sub_tasks.expire_subscription",
            kwargs=json.dumps({"idempotency_key": idempotency_key,
            'purchaser_id': purchaser_id, 'subscription_id': subscription_id}),
            enabled=True)
        return celery_task

    except(pymongo.errors.AutoReconnect,):
        transaction.rollback()
        return create_subscription_task(document=document, idempotency_key=idempotency_key,
        subscription_id=subscription_id, purchaser_id=purchaser_id)

    except(RecursionError) as recursion_exception:
        logger.error('Periodic Subscription Task Has Been Tried To be Created over 1000 times.' % (recursion_exception))
        raise RecursionError

    except(django.core.exceptions.ObjectDoesNotExist,):
        raise django.core.exceptions.ObjectDoesNotExist
