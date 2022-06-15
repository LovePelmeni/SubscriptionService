import pymongo.errors
import datetime
import django.conf, logging
from . import exceptions


# from . import models
try:
    client = pymongo.MongoClient(getattr(django.conf.settings, 'MONGO_DATABASE_URL'), authMechanism='SCRAM-SHA-1')
    sub_database = client['mongo_sub_db']
    collection = sub_database.get_collection(name='sub_collection')
    session = client.start_session()
except(pymongo.errors.ServerSelectionTimeoutError,):
    raise exceptions.MongoDatabaseIsNotRunning()

logger = logging.getLogger(__name__)

# Sub Document Schema:

def upload_new_subscription(subscription):
    try:
        collection.insert_one(document=subscription.dict(), session=session)
        logger.debug('new document with idempotency key %s has been uploaded. time %s' %
        (subscription.idempotency_key, datetime.datetime.now()))

    except(pymongo.collection.InvalidOperation, pymongo.collection.InvalidName):
        logger.error('Invalid Operation or subscription collection does not exist.'
        ' in upload controller.')

def delete_subscription_from_db(key):
    try:
        collection.delete_one(filter={'idempotency_key': key, 'active': True}, session=session)
        logger.debug('document with idempotency_key: %s has been deleted. time: %s' % (key, datetime.datetime.now()))

    except(pymongo.collection.InvalidName, pymongo.collection.InvalidOperation,):
        logger.error('Invalid Operation or Subscription collection does not exist.'
        ' in delete controller.')
        raise NotImplementedError

def delete_all_subscriptions(purchaser_id):
    try:
        collection.delete_many(filter={'purchaser_id': purchaser_id}, session=session)
        logger.debug('all subscriptions for user {%s} has been deleted.')

    except(pymongo.collection.InvalidName, pymongo.collection.InvalidOperation,):
        raise NotImplementedError


def get_subscription_document(key):
    try:
        return collection.find_one(filter={'idempotency_key': key, 'active': True})
    except(pymongo.collection.InvalidName, pymongo.collection.InvalidOperation):
        raise NotImplementedError


def get_subscription_queryset(purchaser_id):
    try:
        return collection.find({'purchaser_id': purchaser_id, 'active': True})
    except(pymongo.collection.InvalidName, pymongo.collection.InvalidOperation):
        raise NotImplementedError()


def mark_as_inactive(idempotency_key):
    try:
        collection.update_one(filter={'idempotency_key': idempotency_key},
        update={'$set': {'active': False}})
        logger.debug('document has been marked as inactive.')
    except(pymongo.collection.InvalidName, pymongo.collection.InvalidOperation):
        raise NotImplementedError





