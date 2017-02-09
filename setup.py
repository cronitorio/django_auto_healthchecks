#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools.command.test import test as TestCommand
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "requests==2.13.0",
    "future==0.16.0"
]

test_requirements = requirements + [
    "pytest",
    "django==1.10.1",
    "mock==2.0.0"
]


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)

setup(
    name='django_auto_healthchecks',
    version='0.1.4',
    description="Create application health checks directly from your django urls.py",
    long_description=readme + '\n\n' + history,
    author="Cronitor.io",
    author_email='support@cronitor.io',
    url='https://github.com/cronitorio/django_auto_healthchecks',
    packages=[
        'django_auto_healthchecks',
    ],
    package_dir={'django_auto_healthchecks':
                 'django_auto_healthchecks'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='django_auto_healthchecks',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests.test_healthchecks',
    tests_require=test_requirements,
    cmdclass={'test': PyTest},
)
