from rest_framework import decorators
from django.db import transaction
import django.db, pydantic, django.core.exceptions
import django.http, logging
from . import models

logger = logging.getLogger(__name__)

@decorators.api_view(['POST'])
@transaction.atomic
def create_customer(request):
    try:
        models.APICustomer.objects.create(**request.data)
        logger.debug('new api customer has been created...')
        return django.http.HttpResponse(status=200)

    except(django.db.IntegrityError,) as int_err:
        logger.error('[API EXCEPTION] %s .could not create user.' % int_err)

    except(pydantic.ValidationError,):
        logger.error('Invalid user credentials has been passed.')

    transaction.rollback()
    return django.http.HttpResponseServerError()

@decorators.api_view(['DELETE'])
@transaction.atomic
def delete_customer(request):
    try:
        models.APICustomer.objects.get(id=request.query_params.get('user_id')).delete()
        return django.http.HttpResponse(status=200)

    except(django.core.exceptions.ObjectDoesNotExist, django.db.IntegrityError,):
        logger.error('[API EXCEPTION]. Could not Delete API Customer')
        transaction.rollback()

    return django.http.HttpResponseServerError()



