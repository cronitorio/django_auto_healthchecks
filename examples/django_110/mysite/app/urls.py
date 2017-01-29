from . import views

# Healthchecks defined inline with your routes are pushed to Cronitor automatically when your Django app starts.
# When settings.DEBUG is True, healthcheck details will be written to stdout and not pushed to Cronitor.

# The django_auto_healthchecks.url method is a drop-in replacement for django.conf.urls.url
from django_auto_healthchecks import url, Healthcheck

urlpatterns = [
    # When no healthcheck param is passed, no healthcheck is created.
    url(r'^tos$',
        views.terms_of_service,
        name='tos'),

    # A simple instance can be used when args or kwargs aren't needed to reverse()
    url(r'^$',
        views.index,
        name='index',
        healthcheck=Healthcheck()),

    # This route will require kwargs to reverse(), so they are passed as part of the Healthcheck
    url(r'^search/(?P<query>.+)$',
        views.search,
        name='search',
        healthcheck=Healthcheck(kwargs={'query': 'Acme'})),

    # All aspects of a healthcheck can be configured inline if desired.
    # Details that are omitted can be managed from the Cronitor dashboard.
    url(r'^api/leads/(?P<lead>.+)$',
        views.api,
        name='leads-detail',
        healthcheck=Healthcheck(
            kwargs={'lead': '12345'},
            name='Lead API Update',
            method='PUT',
            body='{"name": "Spacely Sprockets", "contact": "Cosmo Spacely"}',
            assertions=[{
                'rule_type': 'response_body',
                'operator': 'contains',
                'value': 'Cosmo',
            }]))
]
