#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    @project: authportal
    @component: core
    @copyright: © 2020 by vfabi
    @author: vfabi
    @support: vfabi
    @initial date: 2020-05-23 11:11:23
    @license: this file is subject to the terms and conditions defined
        in file 'LICENSE', which is part of this source code package
    @description:
    @todo:
"""

import os
import logging
from datetime import datetime, timedelta
from pytz import timezone
from jsondb import Database
from cryptography.fernet import Fernet
from flask_simple_captcha import CAPTCHA
from .authbackend import LDAPAuthBackend, MockAuthBackend


def get_variables():
    vs = {}
    vs['flask_secret_key'] = os.urandom(20).hex()
    vs['FLASK_SIMPLE_CAPTCHA_SECRET_CSRF_KEY'] = os.urandom(20).hex()
    vs['db'] = 'var/db.json'
    vs['app_name'] = 'AuthPortal v.1.1'
    vs['LOGGING_LEVEL'] = os.getenv('LOGGING_LEVEL', 'INFO')
    vs['unauthorized_action'] = os.getenv('UNAUTHORIZED_ACTION', 'return_401')  # ['return_302', 'return_401'] return_401 - for Kubernetes
    vs['redirect_url_param_name'] = os.getenv('REDIRECT_URL_PARAM_NAME', 'rd')  # 'rd' - for Kubernetes
    vs['html_form_header'] = os.getenv('HTML_FORM_HEADER', 'Authentication Portal')  # Authentication form header
    vs['auth_backend'] = os.getenv('AUTH_BACKEND', 'ldap')  # ['ldap', 'mock'] Auth backend 
    vs['user_cache_timeout'] = os.getenv('USER_CACHE_TIMEOUT', 10)  # User cache record timeout
    vs['LDAP_SERVER_ADDRESS'] = os.getenv('LDAP_SERVER_ADDRESS', None)  # LDAP server address
    vs['LDAP_SERVER_PORT'] = os.getenv('LDAP_SERVER_PORT', 389)  # LDAP server port
    vs['LDAP_SERVER_USE_SSL'] = os.getenv('LDAP_SERVER_USE_SSL', False)  # [False, True] LDAP server use SSL
    vs['LDAP_SERVER_USER_DN'] = os.getenv('LDAP_SERVER_USER_DN', None)  # LDAP server user DN, example 'cn=admin,dc=example,dc=com'
    vs['LDAP_SERVER_PASSWORD'] = os.getenv('LDAP_SERVER_PASSWORD', None)  # LDAP server user password
    vs['LDAP_SERVER_SEARCH_RDN'] = os.getenv('LDAP_SERVER_SEARCH_RDN', None)  # LDAP server search RDN, example 'ou=Users,dc=example,dc=com'
    return vs

variables = get_variables()


# Auth backend init
authbackends = {
    'ldap': LDAPAuthBackend,
    'mock': MockAuthBackend
}
AuthBackendClass = authbackends[variables['auth_backend']]
authbackend = AuthBackendClass(variables=variables)


# Logging init
logging_levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO
}
logging_level = logging_levels[variables['LOGGING_LEVEL']]


# class MemoryCache:
#     """Basic memory storage cache layer."""

#     def __init__(self, expirationMinutes):
#         self.expirationMinutes = expirationMinutes
#         self.cache = {}
#         self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
#         self.logger = logging.getLogger(__class__.__name__)

#     def add(self, key, value):
#         self.cache[key] = {'value': value, 'ttl': datetime.now() + timedelta(minutes=self.expirationMinutes)}
#         self.logger.debug(f'User object record for username {key} added to cache.')

#     def get(self, key):
#         return self.cache[key]

#     def validate(self, key, value):
#         #if self.validUntil < datetime.now():
#         #    self.cache.pop(key, None)
#         #    self.validUntil = datetime.now() + timedelta(minutes=self.expirationMinutes)
#         if key in self.cache:
#             if self.cache[key]['value'] == value:
#                 ttl = self.cache[key]['ttl']
#                 if ttl > datetime.now():
#                     return True
#         self.logger.debug(f'User object cache record for username {key} was not found or expired.')
#         self.cache.pop(key, None)
#         return False


class Cache:
    """User credentials data Cache.

    Note:
        Stores user's username and password in JSON database to decrease requests count to authentication backend.
        All users password values are stored encrypted only.
        User password stores because of it can be changed anytime at authentication backend side. And this should be handled.
        Thus, credentials should be stored and validated in authentication backend every cache expiration period.
    """

    def __init__(self, expirationMinutes):
        self.expirationMinutes = expirationMinutes
        self.cache = {}
        self.validUntil = datetime.now(timezone('UTC')) + timedelta(minutes=self.expirationMinutes)
        self.logger = logging.getLogger(__class__.__name__)
        self.db = Database(variables['db'])
        self.cryptor = Fernet(Fernet.generate_key())

    def add(self, username, password, password_encrypted):
        if password_encrypted:
            pswd = password
        else:
            pswd = self.cryptor.encrypt(password.encode())
        self.db.data(key=username, value={'password': pswd, 'ttl': datetime.now(timezone('UTC')) + timedelta(minutes=self.expirationMinutes)})
        self.logger.debug(f'User cache record for username {username} has been added.')

    def get(self, username):
        return self.db.data(key=username)

    def validate(self, username, password):
        if username in self.db:
            if self.db.data(key=username)['password'] == password:
                ttl = self.db.data(key=username)['ttl']
                if ttl > datetime.now(timezone('UTC')):
                    return True
        self.logger.debug(f'User cache record for username {username} was not found or expired.')
        self.db.delete(username)
        return False

    def decrypt(self, value):
        return self.cryptor.decrypt(value).decode()


class CustomCaptcha(CAPTCHA):
    """Redefined CAPTCHA from flask_simple_captcha.
    
    Note:
        Redefined because of captcha_html method, to make custom nice form.
    """

    def captcha_html(self, captcha):
        inpu = '<input type="hidden" name="captcha-hash" value="%s">' % captcha['hash']
        img = '<img class="simple-captcha-img" src="data:image/png;base64, %s" />' % captcha['img']
        return '%s\n%s' % (img, inpu)
