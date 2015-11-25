import mongoengine

ROOT_URLCONF = 'parkkeeper.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'parkkeeper',
]

SECRET_KEY = "123"

TIME_ZONE = 'UTC'
USE_TZ = True

TEST_RUNNER = 'djutils.testrunner.TestRunnerWithMongo'

MONGODB = {
    'NAME': 'parkkeeper',
    'HOST': 'localhost',
}
mongoengine.connect(MONGODB['NAME'], tz_aware=True, host='mongodb://%s:27017/%s' % (MONGODB['HOST'], MONGODB['NAME']))

ZMQ_SERVER_ADDRESS = 'localhost'
ZMQ_WORKER_REGISTRATOR_PORT = 5548
ZMQ_EVENT_RECEIVER_PORT = 5549
ZMQ_EVENT_PUBLISHER_PORT = 5550

