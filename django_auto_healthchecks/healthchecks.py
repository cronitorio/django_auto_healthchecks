# -*- coding: utf-8 -*-
from django.conf.urls import url as django_url
from django.core.urlresolvers import reverse
from django.conf import settings
from urllib import urlencode
import base64
import django.urls.exceptions
import hashlib
import json
import logging
import requests

# @todo proper url
ENDPOINT_URL = 'http://dev.cronitor.io/v3/monitors'
DOCS_URL = 'https://cronitor.io/docs/django-healthchecks'

DEFAULTS = {
    'API_KEY': None,
    'VERBOSE': False,
    'HTTPS': False,
    'TEMPLATE': {},
}


class HealthcheckError(RuntimeError):
    pass


class Healthcheck(object):
    """
    Define a healthcheck using a django url route that will be put to the Cronitor API
    """

    def __init__(self, route=None, args=None, kwargs=None, current_app=None, name=None, code=None, method='GET',
                 querystring=None, body=None, headers=None, cookies=None, assertions=None, tags=None, note=None,
                 interval_seconds=None, timeout_seconds=None):
        """
        :param route: str Name of a url route. If omitted, must be set before resolve()
        :param args: list|tuple Optional args to be passed to `reverse()` this route. Cannot be used with `kwargs`.
        :param kwargs: dict Optional kwargs to be passed to `reverse()` this route. Cannot be used with `args`.
        :param current_app:  If the app is namespaced or route name is not unique the `current_app`
               argument is needed for `reverse()`.
        :param name: str Optional name for this monitor. If none is provided, a name will be generated.
        :param code: str Optional monitor code. Use this to tie to an existing healthcheck on your Cronitor dashboard.
        :param method: str Request method used when performing this healthcheck.
        :param querystring: dict Optional querystring parameters that will be appended to the URL
        :param body: str Request body sent when performing this healthcheck if method is PUT, POST or PATCH.
        :param headers: dict Optional request headers that will be sent when performing this healthcheck.
        :param cookies: dict Optional cookies that will be sent when performing this healthcheck.
        :param assertions: dict Optional assertions for this monitor. See API docs for details.
        :param tags: list|tuple Optional tags for this monitor.
        :param note: string Optional note that will be attached to this monitor.
        :param interval_seconds: int Optional interval between healthcheck tests. If omitted, a default will be used.
        :param timeout_seconds: int Optional timeout for this request, maximum of 10 seconds.
        """
        self.route = route
        self.args = args if args else ()
        self.kwargs = kwargs if kwargs else {}
        self.current_app = current_app
        self.name = name
        self.code = code
        self.method = method
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

    def __unicode__(self):
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
        request = {
            'url': self._url.url,
            'method': self.method
        }
        if self.cookies:
            request['cookies'] = self.cookies
        if self.headers:
            request['headers'] = self.headers
        if self.body:
            request['body'] = self.body
        if self.timeout_seconds:
            request['timeout_seconds'] = self.timeout_seconds

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
            definition['rules'] = self.assertions
        if self.interval_seconds:
            definition['request_interval_seconds'] = self.interval_seconds
        if self.tags:
            definition['tags'] = self.tags
        if self.note:
            definition['note'] = self.note

        return dict(_get_setting('TEMPLATE'), **definition)

    def _reverse(self):
        # First, try the route name with a namespace
        reverse_kwargs = {}
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
        return u'{} {}'.format(
            self.method,
            self._url.display
        )

    def _create_code(self):
        """ Generate a unique identifier for this monitor that can be used to update the monitor even if the name
        is changed on the Cronitor dashboard.
        :return: str """
        signature = hashlib.sha1('{}{}'.format(self.is_dev, self.name if self.name else self._defaultName))
        return base64.b64encode(signature.digest()).replace('+', '').replace('/', '')[:12]


class HealthcheckUrl(object):

    url = None
    """ :type unicode Fully qualified URL that will be used in healthcheck """

    display = None
    """ :type unicode Shorter, prettier version of URL for display """

    def __init__(self, path, querystring):
        scheme = 'https://' if _get_setting('HTTPS') else 'http://'
        hostname = self._get_hostname()
        querystring = u'?{}'.format(urlencode(querystring)) if querystring else ''
        self.url = u'{}{}{}{}'.format(scheme, hostname, path, querystring)
        self.display = u'{}{}'.format(hostname, path)

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
        :param Healthcheck healthcheck:
        """
        self._queue.append(healthcheck)

    def drain(self):
        """ Drain enqueued healthchecks and return a list of Healthcheck objects
        :return: List[Healthcheck]"""
        healthchecks = {}
        for healthcheck in self._queue:
            # Routes cannot be reversed at the same time the healthcheck is defined, prepare them for use now.
            healthcheck.resolve()

            if healthcheck.code in healthchecks:
                self._messages.append((logging.WARN, u'Duplicate definition definition for {}, last one wins'.format(
                    str(healthcheck)
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
                (logging.WARN, 'No healthchecks defined. See {} to get started.'.format(DOCS_URL))
            )
        else:
            try:
                payload = [hc.serialize() for hc in healthchecks]
                api_key = _get_setting('API_KEY')

                if api_key:
                    try:
                        r = requests.put(ENDPOINT_URL, json=payload, auth=(api_key, ''), timeout=5)
                        if r.status_code != requests.codes.ok:
                            raise HealthcheckError(r.text)
                    except Exception as e:
                        self._messages.append((
                            logging.ERROR,
                            'Cronitor healthchecks could not be published. Details:\n\n{}'.format(e)
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

                if _get_setting('VERBOSE'):
                    self._messages.append((
                        logging.INFO,
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
    See https://cronitor.io/docs/healthchecks for details.
    :param regex:
    :param view:
    :param healthcheck: Use True for a simple GET healthcheck. Pass a dict to define custom assertions and notifications
    :param kwargs:
    :return:
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
    """ Atomically create/update healthchecks with supplied list of Healthcheck instances. Use this to put healthchecks
    from your deploy script, or add healthchecks for third-party apps without having to modify their code.
    :param healthchecks: list[Healthcheck] of Healthcheck objects These healthchecks will be added to any defined in
           urls.py file(s). See https://cronitor.io/docs/django-healthchecks for details. """
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
