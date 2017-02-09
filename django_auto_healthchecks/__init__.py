# -*- coding: utf-8 -*-
from . import healthchecks

__version__ = '0.1.4'

url = healthchecks.url
""" url is a drop-in replacement for django URL that adds a new healthcheck kwarg """

put = healthchecks.put
""" Optionally, use the put method to batch create/update healthcheck definitions """

HealthcheckError = healthchecks.HealthcheckError
""" :type healthchecks.HealthcheckError Healthcheck definition exception """

Healthcheck = healthchecks.Healthcheck
""" :type healthchecks.Healthcheck """

Client = healthchecks.Client

default_app_config = 'django_auto_healthchecks.apps.HealthchecksAppConfig'
