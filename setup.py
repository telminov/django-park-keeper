# coding: utf-8
# python setup.py sdist register upload
from setuptools import setup

setup(
    name='django-park-keeper',
    version='0.1.5',
    description='Monitoring and services administration.',
    author='Telminov Sergey',
    url='https://github.com/telminov/django-park-keeper',
    packages=[
        'parkkeeper',
        'parkkeeper/datatools',
        'parkkeeper/migrations',
        'parkkeeper/management',
        'parkkeeper/management/commands',
    ],
    license='The MIT License',
    test_suite='runtests.runtests',
    install_requires=[
        'sw-python-utils', 'sw-django-utils', 'django', 'pymongo==3.1', 'mongoengine==0.10.0', 'pyzmq', 'aiohttp',
        'djangorestframework', 'park-worker-base', 'croniter==0.3.11'
    ],
    tests_require=[
        'factory_boy',
    ]
)
