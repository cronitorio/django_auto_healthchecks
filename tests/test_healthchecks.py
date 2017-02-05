#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django_auto_healthchecks.healthchecks` module.
"""

try:
    import mock
except ImportError:
    from unittest import mock

import django_auto_healthchecks.healthchecks as healthchecks
from . import MockSettings


