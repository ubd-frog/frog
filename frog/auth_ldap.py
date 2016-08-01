##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################

"""LDAP auth module"""

import logging

import ldap
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured

LOGGER = logging.getLogger('frog.auth')
LDAP_SUFFIX = getattr(settings, 'LDAP_SUFFIX', '')
LDAP_USERNAME = getattr(settings, 'LDAP_USERNAME')
LDAP_PASSWORD = getattr(settings, 'LDAP_PASSWORD')
LDAP_OPTS = getattr(settings, 'LDAP_OPTIONS', ()) + (
    (ldap.OPT_NETWORK_TIMEOUT, 30),
    (ldap.OPT_REFERRALS, 0),
    (ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3),
)


class LDAPAuthBackend(ModelBackend):
    """
    
    """

    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        for opt, value in LDAP_OPTS:
            ldap.set_option(opt, value)

        username += LDAP_SUFFIX

        try:
            ld = ldap.initialize(settings.LDAP_HOST)
            ld.simple_bind_s(username, password)
        except ldap.LDAPError as e:
            LOGGER.error(e)
            if username != "admin":
                LOGGER.error('Could not log in %s', username)
                LOGGER.error(str(e))

                return None

        user = self.get_or_create(username=username.split('@')[0])[0]

        return user

    def get_or_create(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if LDAP_USERNAME is None or LDAP_PASSWORD is None:
                raise ImproperlyConfigured('LDAP_USERNAME and LDAP_PASSWORD must be set in order to create new users')

            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 30)
            ldap.set_option(ldap.OPT_REFERRALS, 0)  # Required for Active Directory
            ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ld = ldap.initialize(settings.LDAP_HOST)
            ld.simple_bind_s(LDAP_USERNAME, LDAP_PASSWORD)
            # create a new user.  we are using this for the user repository only
            # and not authentication, since that's handled by AD, so we will set the same
            # password for everyone.

            username += LDAP_SUFFIX

            searchFilter = "(&(objectCategory=person)(objectClass=user)(userPrincipalName={0}))"
            results = ld.search_st(
                settings.LDAP_BASE_DN,
                scope=ldap.SCOPE_SUBTREE,
                filterstr=searchFilter.format(username),
                timeout=30
            )

            first_name = results[0][1]['givenName'][0]
            last_name = results[0][1]['sn'][0]
            email = results[0][1]['userPrincipalName'][0]
            # saving user
            user = User(username=results[0][1]['sAMAccountName'][0], password='fake_pass')
            user.is_staff = False
            user.is_superuser = False
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
