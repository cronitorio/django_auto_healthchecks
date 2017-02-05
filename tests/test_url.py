#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks.url` function, a proxy for django `django.conf.urls.url`.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


@mock.patch('django_auto_healthchecks.healthchecks.django_url')
def test_url_calls_django_url(mock_url):
    url_args = ('regex', 'view')
    healthchecks.url(*url_args)
    assert mock_url.call_count == 1, "Mock django_url not called once"
    assert mock_url.call_args == (url_args,), "Args not passed to mock django_url"


@mock.patch('django_auto_healthchecks.healthchecks.Client.enqueue')
@mock.patch('django_auto_healthchecks.healthchecks.django_url')
def test_url_enqueues_healthcheck(mock_url, mock_enqueue):
    healthchecks.settings = MockSettings(DEBUG=True)
    url_args = ('regex', 'view', healthchecks.Healthcheck())
    healthchecks.url(*url_args)
    assert mock_enqueue.call_count == 1, "Mock Client.enqueue not called once"
    assert mock_url.call_count == 1, "Mock django_url not called once"


@mock.patch('django_auto_healthchecks.healthchecks.Client.enqueue')
@mock.patch('django_auto_healthchecks.healthchecks.django_url')
def test_url_strips_healthcheck_before_calling_django_url(mock_url, mock_enqueue):
    healthchecks.settings = MockSettings(DEBUG=True)
    url_args = ('regex', 'view', healthchecks.Healthcheck())
    expected_django_args = ('regex', 'view')
    healthchecks.url(*url_args)
    assert mock_enqueue.call_count == 1, "Mock Client.enqueue not called once"
    assert mock_url.call_count == 1, "Mock django_url not called once"
    assert mock_url.call_args == (expected_django_args,), "Expected args not passed to mock django_url"


def test_url_with_include_raises_exception_when_in_debug_mode():
    healthchecks.settings = MockSettings(DEBUG=True)
    raised = False
    try:
        healthchecks.url('regex', ('included', 'url', 'tuple'), healthchecks.Healthcheck())
    except healthchecks.HealthcheckError:
        raised = True
    finally:
        assert raised, "Expected HealthcheckError exception not raised"


def test_url_with_include_fails_silently_when_not_in_debug_mode():
    healthchecks.settings = MockSettings(DEBUG=False)
    raised = False
    try:
        healthchecks.url('regex', ('included', 'url', 'tuple'), healthchecks.Healthcheck())
    except healthchecks.HealthcheckError:
        raised = True
    finally:
        assert not raised, "Unexpected HealthcheckError exception raised"


@mock.patch('django_auto_healthchecks.healthchecks.Client.enqueue')
@mock.patch('django_auto_healthchecks.healthchecks.django_url')
def test_url_without_healthcheck_param(mock_url, mock_enqueue):
    healthchecks.settings = MockSettings(DEBUG=True)
    url_args = ('regex', 'view')
    healthchecks.url(*url_args)
    assert mock_enqueue.call_count == 0, "Unexpected call to mock Client.enqueue"
    assert mock_url.call_count == 1, "Mock django_url not called once"
    assert mock_url.call_args == (url_args,), "Expected args not passed to mock django_url"


@mock.patch('django_auto_healthchecks.healthchecks.Client.enqueue')
@mock.patch('django_auto_healthchecks.healthchecks.django_url')
def test_route_name_added_to_healthcheck(mock_url, mock_enqueue):
    healthchecks.settings = MockSettings(DEBUG=True)
    route_name = 'test-route'
    healthchecks.url('regex', 'view', healthchecks.Healthcheck(), name=route_name)
    assert mock_enqueue.call_count == 1, "Mock Client.enqueue not called once"
    assert mock_enqueue.call_args[0][0].route == route_name, "Mock Client.enqueue not called once"
