# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible
from future.standard_library import install_aliases
install_aliases()
from django.conf.urls import url as django_url
from django.core.urlresolvers import reverse
from django.conf import settings
from urllib.parse import urlencode
import base64
import django.urls.exceptions
import hashlib
import json
import logging
import requests

ENDPOINT_URL = 'https://cronitor.io/v3/monitors'
DOCS_URL = 'https://cronitor.io/docs/django-health-checks'

DEFAULTS = {
    'API_KEY': None,
    'HTTPS': False,
    'TAGS': [],
}


class HealthcheckError(RuntimeError):
    pass


@python_2_unicode_compatible
class Healthcheck(object):

    def __init__(self, route=None, args=None, kwargs=None, current_app=None, name=None, code=None, method='GET',
                 querystring=None, body=None, headers=None, cookies=None, assertions=None, tags=None, note=None,
                 interval_seconds=None, timeout_seconds=None):
        """ Define a healthcheck using a django url route that will be put to the Cronitor API

                route (str): Name of a url route. If omitted, must be set before resolve().

                args (list|tuple): Optional args to be passed to `reverse()` this route. Cannot be used with `kwargs`.

                kwargs (dict): Optional kwargs to be passed to `reverse()` this route. Cannot be used with `args`.

                current_app (str): If the app is namespaced or route name is not unique the `current_app` argument is
                                    needed for `reverse()`.

                name (str): Optional name for this monitor. If none is provided, a name will be generated.

                code (str): Optional monitor code. Use this to tie to an existing healthcheck on your Cronitor dashboard

                method (str): Request method used when performing this healthcheck.

                querystring (dict): Optional querystring parameters that will be appended to the URL

                body (str): Request body sent when performing this healthcheck if method is PUT, POST or PATCH.

                headers (dict): Optional request headers that will be sent when performing this healthcheck.

                cookies (dict): Optional cookies that will be sent when performing this healthcheck.

                assertions (dict): Optional assertions for this monitor. See API docs for details.

                tags (list|tuple): Optional tags for this monitor.

                note (string): Optional note that will be attached to this monitor.

                interval_seconds (int): Optional interval between healthcheck tests. If omitted, a default will be used.

                timeout_seconds (int): Optional timeout for this request, maximum of 10 seconds.
        """
        self.route = route
        self.args = args if args else ()
        self.kwargs = kwargs if kwargs else {}
        self.current_app = current_app
        self.name = name
        self.code = code
        self.method = method.upper()
        self.querystring = querystring if querystring else {}
        self.body = body
        self.headers = headers
        self.cookies = cookies
        self.assertions = assertions
        self.tags = tags
        self.note = note
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds

        # When in DEBUG mode, create monitors in Dev mode
        self.is_dev = settings.DEBUG

        # These will be defined later during resolve():
        self._url = None
        self._defaultName = None

    def __str__(self):
        return self.name()

    def display_name(self):
        """ Retrieve the effective name of this healthcheck. """
        return self.name if self.name else self._defaultName

    def resolve(self):
        """ Because the route cannot be reversed into a URL at the same time its defined, we delay route resolution
        until we are ready to submit the healthchecks to the API. """
        self._url = HealthcheckUrl(
            path=self._reverse(),
            querystring=self.querystring
        )
        self._defaultName = self._create_name()
        self.code = self.code if self.code else self._create_code()

    def serialize(self):
        """ Serialize current instance details into valid API payload
        :return: dict """

        assert self.method in ('GET', 'POST', 'PUT', 'HEAD', 'OPTIONS', 'PATCH'), \
            "Healthcheck request method must be GET, POST, PUT, HEAD, OPTIONS or PATCH"

        request = {
            'url': self._url.url,
            'method': self.method
        }
        if self.cookies:
            assert isinstance(self.cookies, dict), "Healthcheck request cookies must be a dict"
            request['cookies'] = self.cookies
        if self.headers:
            assert isinstance(self.headers, dict), "Healthcheck request headers must be a dict"
            request['headers'] = self.headers
        if self.timeout_seconds:
            assert isinstance(self.timeout_seconds, int), "Healthcheck request timeout_seconds must be an int"
            request['timeout_seconds'] = self.timeout_seconds
        if self.body:
            request['body'] = self.body

        definition = {
            'type': 'healthcheck',
            'code': self.code,
            'defaultName': self._defaultName,
            'request': request,
            'dev': self.is_dev
        }

        if self.name:
            definition['name'] = self.name

        if self.assertions:
            assert isinstance(self.assertions, (list, tuple, set)), \
                "Healthcheck assertions must be a list, tuple or set"
            definition['rules'] = self.assertions

        if self.interval_seconds:
            assert isinstance(self.interval_seconds, int), \
                "Healthcheck interval_seconds must be an int"
            definition['request_interval_seconds'] = self.interval_seconds

        if self.tags:
            assert isinstance(self.tags, (list, tuple, set)), \
                "Healthcheck tags must be in a list, tuple or set"
            definition['tags'] = set(self.tags + _get_setting('TAGS'))
        elif _get_setting('TAGS'):
            assert isinstance(_get_setting('TAGS'), (list, tuple, set)), \
                "settings.HEALTHCHECKS['TAGS'] must be a list, tuple or set"
            definition['tags'] = _get_setting('TAGS')

        if self.note:
            definition['note'] = self.note

        return definition

    def _reverse(self):
        # The reverse() method accepts either kwargs or args, not both

        reverse_kwargs = {}
        if self.kwargs and self.args and settings.DEBUG:
            raise HealthcheckError(
                'Cannot reverse route "{}" with both args and kwargs.'.format(self.display_name())
            )

        if self.kwargs:
            reverse_kwargs['kwargs'] = self.kwargs
        elif self.args:
            reverse_kwargs['args'] = self.args

        if self.current_app:
            reverse_kwargs['current_app'] = self.current_app

        try:
            return reverse(self.route, **reverse_kwargs)
        except django.urls.exceptions.NoReverseMatch:
            raise HealthcheckError(
                'Could not reverse route for {}. '
                'Provide a `current_app` hint in your healthcheck definition.'.format(self.route)
            )

    def _create_name(self):
        """ Create a default name e.g. GET www.example.com/login
        :return: str """
        return '{} {}'.format(
            self.method,
            self._url.display
        )

    def _create_code(self):
        """ Generate a unique identifier for this monitor that can be used to update the monitor even if the name
        is changed on the Cronitor dashboard. Include is_dev in the hash to differentiate between dev and prod
        versions of a monitor
        :return: str """
        env = 'dev' if self.is_dev else 'prod'
        signature = hashlib.sha1(env.encode() + self._defaultName.encode())
        hash = base64.b64encode(signature.digest())
        return str(hash[:12]).replace('+', '').replace('/', '')


class HealthcheckUrl(object):

    url = None
    """ :type unicode Fully qualified URL that will be used in healthcheck """

    display = None
    """ :type unicode Shorter, prettier version of URL for display """

    def __init__(self, path, querystring):
        scheme = 'https://' if _get_setting('HTTPS') else 'http://'
        hostname = self._get_hostname()
        querystring = '?{}'.format(urlencode(querystring)) if querystring else ''
        self.url = '{}{}{}{}'.format(scheme, hostname, path, querystring)
        self.display = '{}{}'.format(hostname, path)

    def _get_hostname(self):
        """ Try to determine the hostname to use when making the healthcheck request
        :return: string
        :raises HealthcheckError """

        # First look in settings.HEALTHCHECKS['HOSTNAME']
        try:
            if _get_setting('HOSTNAME'):
                return _get_setting('HOSTNAME')
        except HealthcheckError:
            pass

        # Then try settings.HOSTNAME, if it exists
        try:
            if hasattr(settings, 'HOSTNAME') and len(settings.HOSTNAME):
                return settings.HOSTNAME
        except (AttributeError, TypeError):
            pass

        # Finally, pop the first value from settings.ALLOWED_HOSTS
        try:
            if hasattr(settings, 'ALLOWED_HOSTS') and len(settings.ALLOWED_HOSTS):
                return settings.ALLOWED_HOSTS[0]
        except (AttributeError, TypeError, KeyError):
            pass

        raise HealthcheckError(
            'Error: Could not determine hostname from settings.HEALTHCHECKS["HOSTNAME"], '
            'settings.HOSTNAME or settings.ALLOWED_HOSTS'
        )


class IdempotentHealthcheckClient(object):
    """
    Put enqueued healthchecks to the Cronitor API.
    """
    _queue = None
    """ We cannot `reverse()` a route at the same time the `url()` method is called. Queue healthchecks for later.
    :type list """

    _messages = None
    """ Messages written to a `django_auto_healthchecks.healthchecks` logger
    :type list """

    def __init__(self):
        self._queue = []
        self._messages = []

    def enqueue(self, healthcheck):
        """ Add a healthcheck instance to a queue for later processing.
        healthcheck (Healthcheck): Healthcheck instance to enqueue
        """
        self._queue.append(healthcheck)

    def drain(self):
        """ Drain enqueued healthchecks and return a list of distinct Healthcheck objects
        :return: List[Healthcheck]"""
        healthchecks = {}
        for healthcheck in self._queue:
            healthcheck.resolve()
            if healthcheck.code in healthchecks:
                self._messages.append((logging.WARN, 'Duplicate definition definition for {}, last one wins'.format(
                    healthcheck.display_name()
                )))

            healthchecks[healthcheck.code] = healthcheck

        self._queue = []
        return healthchecks.values()

    def put(self, additional_healthchecks=None):

        # If healthchecks have been defined in a batch and passed here, add them to the queue containing any
        # checks defined in urls.py file(s)
        map(self.enqueue, (additional_healthchecks or ()))
        healthchecks = self.drain()

        if len(healthchecks) == 0:
            self._messages.append(
                (logging.WARN, 'No health checks defined. See {} to get started.'.format(DOCS_URL))
            )
        else:
            try:
                payload = []
                for healthcheck in healthchecks:
                    try:
                        payload.append(healthcheck.serialize())
                    except AssertionError as e:
                        self._messages.append((
                            logging.ERROR,
                            'Healthcheck can not be published. Validation error: {}'.format(e)
                        ))

                api_key = _get_setting('API_KEY')
                if api_key:
                    try:
                        r = requests.put(ENDPOINT_URL, json=payload, auth=(api_key, ''), timeout=5)
                        if r.status_code != requests.codes.ok:
                            raise HealthcheckError(r.text)
                    except Exception as e:
                        self._messages.append((
                            logging.ERROR,
                            'Cronitor healthchecks could not be published. Request failure. Details:\n\n{}'.format(e)
                        ))
                else:
                    self._messages.append((
                        logging.ERROR,
                        'Missing Cronitor API key. Set settings.HEALTHCHECKS["API_KEY"] to publish healthchecks.'
                    ))

                if settings.DEBUG:
                    self._messages.append((
                        logging.INFO,
                        'DEV MODE: settings.DEBUG is True. Monitors will be created in Dev mode.'
                    ))

                self._messages.append((
                    logging.DEBUG,
                    'PUT {}:\n{}\n\n'.format(ENDPOINT_URL, json.dumps(payload, indent=2))
                ))

            except HealthcheckError as e:
                self._messages.append((logging.ERROR, str(e)))

        self._flush_messages_to_log()

    def _flush_messages_to_log(self):
        """ Write messages to the `django_auto_healthchecks.healthchecks` logger """
        logging.basicConfig()
        logger = logging.getLogger(__name__)
        [logger.log(msg[0], msg[1]) for msg in self._messages]
        self._messages = []


def url(regex, view, healthcheck=None, **kwargs):
    """ Drop-in replacement for django.conf.urls.url to create and update a Cronitor healthcheck when your app restarts.
    See https://cronitor.io/docs/django-health-checks for details.
    regex (str): Route regex, passed to `django.conf.urls.url()`
    view (mixed): Attached view for this route, passed to `django.conf.urls.url()`
    healthcheck (Healthcheck): Define your healthcheck with a `Healthcheck()` instance.
    :return RegexURLPattern
    """

    if isinstance(healthcheck, Healthcheck):
        if isinstance(view, (list, tuple)):
            if settings.DEBUG:
                raise HealthcheckError('Healthchecks must be defined on individual routes')
        else:
            healthcheck.route = kwargs.get('name')
            Client.enqueue(healthcheck)

    return django_url(regex, view, **kwargs)


def put(healthchecks=()):
    """ Batch create-or-update health checks with supplied list of Healthcheck instances. Invoke from your deploy
    script, or add healthchecks for third-party apps without having to hack their code.
    :param healthchecks: list[Healthcheck] of Healthcheck objects These healthchecks will be merged with any defined in
           urls.py file(s). See https://cronitor.io/docs/django-health-checks for details. """
    Client.put(healthchecks)


def _get_setting(key):
    """ For any given setting, look in the HEALTHCHECKS key of the django settings object and global key in settings obj.
    If it's not there, look for default in DEFAULTS
    :param key: Name of setting
    :return: * """
    if hasattr(settings, 'HEALTHCHECKS') and key in settings.HEALTHCHECKS:
        return settings.HEALTHCHECKS[key]

    if key in DEFAULTS:
        return DEFAULTS[key]

    raise HealthcheckError('Error: Could not find setting key {}'.format(key))


Client = IdempotentHealthcheckClient()
