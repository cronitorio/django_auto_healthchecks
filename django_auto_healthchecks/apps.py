# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.core.urlresolvers import reverse
import django.urls.exceptions
from . import healthchecks


class HealthchecksAppConfig(AppConfig):
    """ Attach into the Django app startup.
    At this point the URL resolver cache has not been warmed yet. """
    name = 'django_auto_healthchecks'

    def ready(self):
        try:
            reverse('request-a-route-to-parse-urls-and-populate-healthchecks')
        except django.urls.exceptions.NoReverseMatch:
            pass
        finally:
            # Any healthecks defined in urls.py will be parsed and ready to PUT now.
            healthchecks.put()
