#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks.HealthcheckUrl` class.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


def test_hostname_from_healthcheck_settings():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname})
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert test_hostname in HcUrl.url, "URL does not contain expected hostname"


def test_hostname_detection_fallback_to_settings_hostname():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(HOSTNAME=test_hostname)
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert test_hostname in HcUrl.url, "URL does not contain expected hostname"


def test_hostname_detection_fallback_to_allowed_hosts():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(ALLOWED_HOSTS=(test_hostname,))
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert test_hostname in HcUrl.url, "URL does not contain expected hostname"


def test_raise_exception_when_hostname_cannot_be_detected():
    healthchecks.settings = MockSettings()
    raised = False
    try:
        HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    except healthchecks.HealthcheckError:
        raised = True
    finally:
        assert raised, "Expected HealthcheckError exception not raised"


def test_url_contains_all_expected_parts():
    test_hostname = 'cronitor.io'
    test_path = '/path/to/endpoint'
    test_querystring = {
        'foo': 'bar',
        'bar': 'foo'
    }
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname, 'HTTPS': False})
    HcUrl = healthchecks.HealthcheckUrl(test_path, test_querystring)
    assert 'foo=bar&bar=foo' in HcUrl.url, "URL does not contain querystring"
    assert 'http' in HcUrl.url, "URL does not contain scheme"
    assert test_hostname in HcUrl.url, "URL does not contain hostname"
    assert test_path in HcUrl.url, "URL does not contain path"


def test_https_enabled_healthcheck_settings():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname, 'HTTPS': True})
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert test_hostname in HcUrl.url, "URL does not contain expected hostname"
    assert 'https://' in HcUrl.url, "URL does not contain https://"


def test_https_disabled_healthcheck_settings():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname, 'HTTPS': False})
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert test_hostname in HcUrl.url, "URL does not contain expected hostname"
    assert 'http://' in HcUrl.url, "URL does not contains http://"


def test_https_disabled_by_default():
    test_hostname = 'cronitor.io'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname})
    HcUrl = healthchecks.HealthcheckUrl('/path/to/endpoint', None)
    assert 'http://' in HcUrl.url, "URL does not contains http://"


def test_querystring_in_url_not_display_url():
    test_hostname = 'cronitor.io'
    test_path = '/path/to/endpoint'
    test_querystring = {
        'foo': 'bar',
        'bar': 'foo'
    }
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': test_hostname, 'HTTPS': False})
    HcUrl = healthchecks.HealthcheckUrl(test_path, test_querystring)
    assert 'foo=bar&bar=foo' in HcUrl.url, "URL does not contains querystring"
    assert 'foo=bar&bar=foo' not in HcUrl.display, "Display URL unexpectedly containss querystring"
