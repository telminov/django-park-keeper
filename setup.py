# coding: utf-8
# python setup.py sdist register upload
from distutils.core import setup

setup(
    name='django-park-keeper',
    version='0.0.2',
    description='Monitoring and services administration.',
    author='Telminov Sergey',
    url='https://github.com/telminov/django-park-keeper',
    packages=['parkkeeper',],
    license='The MIT License',
    install_requires=[
        'django', 'mongoengine', 'pyzmq', 'aiohttp', 'djangorestframework', 'park-worker-base'
    ],
)
