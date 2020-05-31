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

import logging
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE


class AuthBackend:

    def __init__(self, variables):
        self.variables = variables
        self.logger = logging.getLogger(__class__.__name__)

    def auth(self, username, password):
        raise Exception('NotImplementedException')


class LDAPAuthBackend(AuthBackend):
    """LDAPv3 authentication backend."""

    def __init__(self, variables):
        super().__init__(variables)
        self.variables = variables
        use_ssl = True if variables['LDAP_SERVER_USE_SSL'] == "True" else False
        self.server = Server(
            variables['LDAP_SERVER_ADDRESS'],
            port=int(variables['LDAP_SERVER_PORT']),
            use_ssl=use_ssl,
            get_info=ALL
        )

    def auth(self, username, password):
        return self.process(username, password)

    def process(self, username, password):
        self.logger.debug(f'Processing authentication request for username {username} to {__class__.__name__}.')
        if username == '' or username is None:
            raise Exception('Field username is empty')
        if password == '' or password is None:
            raise Exception('Field password is empty')

        try:
            ldap = Connection(self.server, self.variables['LDAP_SERVER_USER_DN'], self.variables['LDAP_SERVER_PASSWORD'], auto_bind=True)
            if ldap.search(self.variables['LDAP_SERVER_SEARCH_RDN'], f'(&(objectclass=inetOrgPerson)(cn={username}))'):
                user_dn = ldap.response[0]['dn']
                ldap.unbind()
                ldap = Connection(self.server, user_dn, password)
                if ldap.bind():
                    self.logger.debug(f'{__class__.__name__} result: user with username {username} successfully bind(authentication) in LDAP server. Response: {ldap.result}')
                    ldap.unbind()
                    return True
                self.logger.debug(f'{__class__.__name__} result: user with username {username} bind(authentication) in LDAP server unsuccessful. Response: {ldap.result}')
            else:
                self.logger.debug(f'{__class__.__name__} result: user with username {username} was not found.')
        except Exception as e:
            self.logger.error(f'{__class__.__name__} Exception. Details: {e}')
        return False


class MockAuthBackend(AuthBackend):
    """Mockup authentication backend."""

    def auth(self, username, password):
        self.logger.debug(f'Received user credentials: username {username}, password {password}')
        return True
