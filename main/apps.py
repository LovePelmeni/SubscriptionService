import os

from django.apps import AppConfig
from health_check import plugins
import time

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from . import\
        healthcheck, signals, initial_migrations
        plugins.plugin_dir.register(healthcheck.CeleryHealthCheckAPIBackend)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Analytic.settings')


