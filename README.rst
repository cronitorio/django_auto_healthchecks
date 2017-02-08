========================
Django Auto Healthchecks
========================

.. image:: https://img.shields.io/pypi/v/django_auto_healthchecks.svg
        :target: https://pypi.python.org/pypi/django_auto_healthchecks

.. image:: https://img.shields.io/travis/cronitorio/django_auto_healthchecks.svg
        :target: https://travis-ci.org/cronitorio/django_auto_healthchecks

.. image:: https://readthedocs.org/projects/django-auto-healthchecks/badge/?version=latest
        :target: https://django-auto-healthchecks.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



Create application healthchecks directly from your Django ``urls.py`` with Cronitor.io and ``django_auto_healthchecks``.

- Define health checks directly from your code, push them to Cronitor in a single request when your app starts
- Healthchecks are run instantly after a deploy and as often as every 30 seconds from Cronitor systems in the United States, Europe and Asia.
- Create powerful assertions like ``response_body contains 'OK'`` and ``response_time < 5 seconds``. Be notified instantly if assertions fail.
- Ensure the right people are notified of downtime with alerts in Slack, PagerDuty, HipChat, Email and SMS.

Getting Started
---------------

- Implementation guide: https://cronitor.io/docs/django-healthchecks
- Package documentation: https://django-auto-healthchecks.readthedocs.io.


This package was cut with Cookiecutter: https://github.com/audreyr/cookiecutter

