#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks.Healthcheck` class.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import pytest
import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


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


def test_dev_mode_when_debug_true():
    pass


def test_dev_mode_false_when_debug_false():
    pass


def test_dev_mode_changes_generated_code():
    pass


def test_name_change_does_not_change_generated_code():
    pass


@mock.patch('django_auto_healthchecks.healthchecks.resolve')
def test_url_resolve_call(mock_resolve):
    pass


@mock.patch('django_auto_healthchecks.healthchecks.resolve')
def test_url_resolve_call_includes_current_app_when_provided(mock_resolve):
    pass


def test_monitor_tags_merged_with_settings_tags():
    pass


def test_serialized_payload_includes_important_parts():
    pass
