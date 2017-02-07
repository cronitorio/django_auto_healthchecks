#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks.IdempotentHealthcheckClient` class.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import pytest
import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


class MockRequestsResponse(object):

    def __init__(self, status_code):
        self.status_code = status_code


@pytest.fixture
def healthcheck_instance():
    def mock_resolve(self):
        self._url = healthchecks.HealthcheckUrl(
            path='/path/to',
            querystring={}
        )
        self._defaultName = self._create_name()
        self.code = self.code if self.code else self._create_code()

    healthchecks.settings = MockSettings(HEALTHCHECKS={'API_KEY': 'this is a key'}, DEBUG=True)
    instance = healthchecks.Healthcheck()
    instance.resolve = lambda: mock_resolve(instance)
    return instance


@mock.patch('django_auto_healthchecks.healthchecks.requests.put')
def test_put_invokes_request(mock_put, healthcheck_instance):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'API_KEY': 'this is a key'}, DEBUG=True, HOSTNAME='cronitor.io')
    healthchecks.Client.enqueue(healthcheck_instance)
    healthchecks.Client.put()
    assert mock_put.call_count == 1, "requests.put not called once"


@mock.patch('django_auto_healthchecks.healthchecks.requests.put')
def test_put_does_not_invoke_request_without_api_key(mock_put, healthcheck_instance):
    healthchecks.settings = MockSettings(HEALTHCHECKS={}, DEBUG=True, HOSTNAME='cronitor.io')
    healthchecks.Client.enqueue(healthcheck_instance)
    healthchecks.Client.put()
    assert mock_put.call_count == 0, "Unexpected call to requests.put"


@mock.patch('django_auto_healthchecks.healthchecks.requests.put', return_value=MockRequestsResponse(status_code=500))
def test_request_failure_raises_healthcheck_error(mock_put, healthcheck_instance):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'API_KEY': 'this is a key'}, DEBUG=False, HOSTNAME='cronitor.io')
    healthchecks.Client.enqueue(healthcheck_instance)
    healthchecks.Client._flush_messages_to_log = lambda: ''
    healthchecks.Client.put()
    assert mock_put.call_count == 1, "requests.put not called once"
    assert 'Request failure' in healthchecks.Client._messages[0][1], \
        "Expected an error with 'Request failure', got '{}'".format(healthchecks.Client._messages[0][1])


def test_drain_queue_drains_the_queue(healthcheck_instance):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'API_KEY': 'this is a key'}, DEBUG=True, HOSTNAME='cronitor.io')
    healthchecks.Client.enqueue(healthcheck_instance)

    assert len(healthchecks.Client.drain()) > 0, "Expected enqueued healthcheck from drain()"
    assert len(healthchecks.Client.drain()) == 0, "Expected empty drain() on second attempt"


