#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks.Healthcheck` class.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import json
import pytest
import re
import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_dev_mode_when_debug_true(mock_reverse):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    payload = healthcheck.serialize()
    assert mock_reverse.call_count == 1, "Expected reverse() call once"
    assert 'dev' in payload, "Serialized payload missing 'dev' field"
    assert payload['dev'], "Expected dev to be True"

@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_dev_mode_false_when_debug_false(mock_reverse):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=False)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    payload = healthcheck.serialize()
    assert mock_reverse.call_count == 1, "Expected reverse() call once"
    assert 'dev' in payload, "Serialized payload missing 'dev' field"
    assert not payload['dev'], "Expected dev to be False"

@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_dev_mode_changes_generated_key(mock_reverse):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    devKey = healthcheck.key

    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=False)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    prodKey = healthcheck.key

    assert devKey != prodKey, "Expected DEBUG flag to change generated job key"

@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_name_change_does_not_change_generated_key(mock_reverse):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    devKey = healthcheck.key
    healthcheck = healthchecks.Healthcheck(name="Something better than the default name")
    healthcheck.resolve()
    prodKey = healthcheck.key

    assert devKey == prodKey, "Name change should not affect produced job key"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_generated_key_contains_only_valid_chars(mock_reverse):
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    healthcheck = healthcheck.serialize()
    healthcheck = json.loads(json.dumps(healthcheck))

    assert re.compile(r'[A-Za-z0-9]').match(healthcheck['key']), "Invalid healthcheck key: {}".format(healthcheck['key'])

@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_url_resolve_call(mock_reverse):
    route_name = 'example-route-name'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck(route=route_name)
    healthcheck.resolve()
    payload = healthcheck.serialize()
    assert mock_reverse.call_args == ((route_name,),), "Args not passed to mock django_url"
    assert '/path/to/endpoint' in payload['request']['url'], "Expected reverse() return path in generated request URL"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_url_resolve_call_includes_current_app_when_provided(mock_reverse):
    route_name = 'example-route-name'
    current_app = 'example-app-name'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck(route=route_name, current_app=current_app)
    healthcheck.resolve()

    expected_args = ((route_name,), {'current_app': 'example-app-name'})
    assert mock_reverse.call_args == expected_args, "Args not passed to mock django_url"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_url_resolve_call_raises_error_with_both_args_and_kwargs(mock_reverse):
    route_name = 'example-route-name'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=True)
    healthcheck = healthchecks.Healthcheck(
        route=route_name,
        args=('a', 'b'),
        kwargs={'a': 1, 'b': 2}
    )

    raised = False
    try:
        healthcheck.resolve()
    except healthchecks.HealthcheckError:
        raised = True
    finally:
        assert raised, "Expected HealthcheckError for using args and kwargs"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_url_resolve_call_raises_no_error_with_both_args_and_kwargs_when_debug_false(mock_reverse):
    route_name = 'example-route-name'
    healthchecks.settings = MockSettings(HEALTHCHECKS={'HOSTNAME': 'cronitor.io'}, DEBUG=False)
    healthcheck = healthchecks.Healthcheck(
        route=route_name,
        args=('a', 'b'),
        kwargs={'a': 1, 'b': 2}
    )

    raised = True
    try:
        healthcheck.resolve()
    except healthchecks.HealthcheckError:
        raised = False
    finally:
        assert raised, "Expected HealthcheckError for using args and kwargs"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_monitor_tags_merged_with_settings_tags(mock_reverse):
    first_tags = ['Django', 'ExampleApp']
    second_tags = ['LandingPages', 'Django']
    merged_tags = ['Django', 'ExampleApp', 'LandingPages']

    healthchecks.settings = MockSettings(
        HEALTHCHECKS={'HOSTNAME': 'cronitor.io', 'TAGS': first_tags},
        DEBUG=False
    )
    healthcheck = healthchecks.Healthcheck(tags=second_tags)
    healthcheck.resolve()
    payload = healthcheck.serialize()
    assert set(payload['tags']) == set(merged_tags), "Tags not merged as expected"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_serialized_payload_includes_default_parts(mock_reverse):
    healthchecks.settings = MockSettings(
        HEALTHCHECKS={'HOSTNAME': 'cronitor.io'},
        DEBUG=False
    )
    healthcheck = healthchecks.Healthcheck()
    healthcheck.resolve()
    payload_keys = healthcheck.serialize().keys()
    assert 'dev' in payload_keys, "Request payload should have 'dev' field"
    assert 'request' in payload_keys, "Request payload should have 'request' field"
    assert 'key' in payload_keys, "Request payload should have 'key' field"
    assert 'defaultName' in payload_keys, "Request payload should have 'defaultName' field"
    assert 'type' in payload_keys, "Request payload should have 'type' field"


@mock.patch('django_auto_healthchecks.healthchecks.reverse', return_value='/path/to/endpoint')
def test_serialized_payload_includes_optional_parts(mock_reverse):
    healthchecks.settings = MockSettings(
        HEALTHCHECKS={'HOSTNAME': 'cronitor.io'},
        DEBUG=False
    )
    healthcheck = healthchecks.Healthcheck(name='Example Name', tags=['tag1'], note='Example Note', assertions=[{
        'rule_type': 'response_body',
        'operator': 'contains',
        'value': 'Cosmo',
    }])
    healthcheck.resolve()
    payload_keys = healthcheck.serialize().keys()
    assert 'rules' in payload_keys, "Request payload should have 'rules' field"
    assert 'tags' in payload_keys, "Request payload should have 'tags' field"
    assert 'note' in payload_keys, "Request payload should have 'note' field"
    assert 'name' in payload_keys, "Request payload should have 'name' field"
