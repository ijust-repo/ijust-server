# -*- coding: utf-8 -*-

# python imports
import random
import string
import os


class DefaultConfig(object):
    # app

    DEFAULT_APP_NAME = 'ijust'
    DEBUG = True
    TESTING = True
    DEPLOYMENT = False
    TRAP_HTTP_EXCEPTIONS = True
    TOKEN_EXPIRE_TIME = 5 * 3600

    # directory

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SCHEMA_DIR = os.path.join(BASE_DIR, 'schemas')
    TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
    MEDIA_DIR = os.path.join(TEMP_DIR, 'Media')
    PROBLEM_DIR = os.path.join(MEDIA_DIR, 'Problems')
    TESTCASE_DIR = os.path.join(MEDIA_DIR, 'Testcases')
    SUBMISSION_DIR = os.path.join(MEDIA_DIR, 'Submissions')

    # form

    WTF_CSRF_ENABLED = False
    CSRF_ENABLED = False

    # upload

    MAX_CONTENT_LENGTH = 4 * 1024 * 1024

    # cache

    CACHE_TYPE = 'null'
    CACHE_DEFAULT_TIMEOUT = 900
    CACHE_THRESHOLD = 100
    CACHE_NO_NULL_WARNING = True
    CACHE_DIR = os.path.join(TEMP_DIR, 'Cache')

    # redis

    REDIS_URL = "redis://localhost:6379/0"

    # celery

    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # mongo

    MONGODB_SETTINGS = {
        'db': 'ijust',
        'host': '127.0.0.1',
        'port': 27017
    }


class DevelopmentConfig(DefaultConfig):
    # app

    TESTING = False

    # cache

    CACHE_TYPE = 'filesystem'


class DeploymentConfig(DefaultConfig):
    # app

    DEBUG = False
    DEPLOYMENT = True

    # cache

    CACHE_TYPE = 'redis'


class TestingConfig(DefaultConfig):
    # app

    DEBUG = True
    TESTING = True

    # cache

    CACHE_TYPE = 'filesystem'
