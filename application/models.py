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

import base64
import logging
from .utils import authbackend, Cache, variables


cache = Cache(variables['user_cache_timeout'])


class User:
    """User model.

    Note:
        Includes some required by flask_login attrs and methods.
    """

    is_active = False
    is_authenticated = False
    is_anonymous = False

    def __init__(self, **initkwargs):
        self.username = initkwargs.get('username', None)
        self.password = initkwargs.get('password', None)
        self.id = initkwargs.get('id', None)
        self.logger = logging.getLogger(__class__.__name__)

    @classmethod
    def get(cls, username, password):
        c = cls(username=username, password=password)
        c.action = 'get_auth'
        c.password_encrypted = False
        c.is_authenticated = c.auth()
        c.is_active = c.is_authenticated
        return c

    @classmethod
    def check(cls, id):
        c = cls(id=id)
        c.action = 'check_auth'
        c.password_encrypted = True
        c.username, c.password = c._get_cached_user()
        c.is_authenticated = c.auth()
        c.is_active = c.is_authenticated
        return c

    def auth(self):
        if not self.username:
            return False
        self.logger.debug(f'Authentication request for username {self.username}.')

        if self.action == 'check_auth':
            if cache.validate(self.username, self.password):
                self.logger.debug(f'User record for username {self.username} was found in cache.')
                return True

        password = cache.decrypt(self.password) if self.password_encrypted else self.password
        auth = authbackend.auth(self.username, password)

        if auth:
            self.logger.info(f'User with username {self.username} successfully authenticated.')
            cache.add(self.username, self.password, password_encrypted=self.password_encrypted)
        else:
            self.logger.info(f'User with username {self.username} authentication failed.')
        return auth

    def _get_cached_user(self):
        username = base64.b64decode(self.id).decode('utf-8')
        cached_user = cache.get(username)
        if cached_user:
            return username, cached_user['password']
        return None, None

    def get_id(self):
        return base64.b64encode(self.username.encode()).decode('utf-8')
