#!/bin/sh

set -e

echo "Checking for migrations..."
python manage.py makemigrations
sleep 5
if [$? -ne 0]; then
    echo "Failed to make migrations. Looks Like PostgresSQL Database is not connected."
    exit 1;
fi

echo "Migrating..."

python manage.py migrate
sleep 5
echo "Migrated."
if [$? -ne 0]; then
echo "Failed to migrate to the database."
exit 1;
fi

echo "Creating Superuser...."

echo 'from django.contrib.auth import get_user_model;
user = get_user_model();
user.objects.create_superuser(username="Superuser",
email="Superuser@gmail.com", password="Password")' | python manage.py shell

echo "Running Services Integration Tests."
python manage.py test main.services_integration_tests

  if [$? -ne 0]; then
    echo "Failed to start celery worker. Exiting..."
    exit 1;
    else continue
  fi
echo "Run..."

echo "Running Celery..."
celery -A Analytic worker -l info &

  if [$? -ne 0]; then
    echo "Failed to start celery worker. Exiting..."
    exit 1;
    else continue
  fi

echo "Running Celery Beat Worker..."
celery -A Analytic beat -l info &

echo "Run Successfully."

if [$? -ne 0]; then
echo "Failed to Start Celery Beat Worker. Exiting..."
exit 1;
fi


echo "Superuser has been created successfully."

# This method responsible for running API Endpoint Tests.
echo "Running  Unittests..."
python manage.py test
if [$? -ne 0]; then
echo "Unittests failed. Exiting..."
exit 1;
fi

echo "Unittests has executed with success response. Running Celery..."
sleep 5

echo "Running Gunicorn..."
gunicorn Analytic.wsgi:application --bind 0.0.0.0:8076 --workers 5 --timeout 120

echo "Gunicorn server has started. Application Configured."




