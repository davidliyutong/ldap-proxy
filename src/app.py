# -*- coding: utf-8 -*-

from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from ldap3.utils.hashed import hashed
from ldap3 import (
    HASHED_SALTED_SHA, MODIFY_REPLACE, HASHED_SALTED_SHA256
)

import json
import os
import base64
from flask import (
    Flask,
    Response,
    request,
    render_template,
    redirect,
    jsonify,
    make_response,
    url_for,
    abort,
)
from flask_httpauth import HTTPBasicAuth


def status_code(code):
    return Response(status=code)


# Pass environment variables
ldap_host = os.getenv("LDAP_HOST")
port = os.getenv("LDAP_PORT")
base_dn = os.getenv("LDAP_BASE_DN")
user = os.getenv("LDAP_BIND_USER")
password = os.getenv("LDAP_BIND_PASSWORD")
# example: uid={0},ou=users,dc=xxxxx,dc=com
user_dn = os.getenv("LDAP_USER_DN")
search_dn = os.getenv("LDAP_SEARCH_DN")  # example: (uid={0})

app = Flask(__name__)
auth = HTTPBasicAuth()


class LdapUtils(object):
    def __init__(self, ldap_host=None, port=None, base_dn=None, user=None, password=None):
        self.ldap_host = ldap_host
        self.port = port
        self.base_dn = base_dn
        self.user = user
        self.password = password

        self.initiate_connection()

    def initiate_connection(self):
        print('LdapUtils.ldap_search_dn connect:' + 'ldap_host:' + str(self.ldap_host) + ' port:' + str(self.port) + ' base_dn:' + str(self.base_dn) + ' user:' + str(self.user))
        try:
            server = Server(self.ldap_host, self.port, get_info=ALL)
            self.ldapconn = Connection(server, user=None, password=None,
                                       auto_bind='NONE', version=3, authentication='SIMPLE',
                                       client_strategy='SYNC',
                                       auto_referrals=True, check_names=True, read_only=False, lazy=False,
                                       raise_exceptions=False)
            self.ldapconn.rebind(user=self.user, password=self.password)
        except Exception as e:
            print('LdapUtils.initiate_connection exception:' + str(e))

    def ldap_search_dn(self, uid=None, is_retry=False):
        obj = self.ldapconn
        search_base = self.base_dn
        search_scope = SUBTREE
        search_filter = search_dn.format(uid)
        try:
            obj.search(search_base, search_filter, search_scope,
                       attributes=['cn', 'userPassword'], paged_size=1)
            if len(obj.response) == 1:
                return obj.response[0]['dn']
            else:
                return None
        except Exception as e:
            print('LdapUtils.ldap_search_dn exception:' + str(e))
            if not is_retry:
                self.initiate_connection()
                return self.ldap_search_dn(uid, True)
            else:
                return None

    def ldap_get_vaild(self, uid=None, passwd=None):
        if not uid or not passwd:
            return False

        obj = self.ldapconn

        dn = self.ldap_search_dn(uid)
        if dn is None:
            return False

        try:
            if obj.rebind(dn, passwd):
                return True
            else:
                return False
        except Exception as e:
            print('LdapUtils.ldap_get_vaild exception:' + str(e))


ldap = LdapUtils(ldap_host, int(port), base_dn, user, password)


@auth.error_handler
def auth_error(status):
    return status_code(401)


def ldap_verify_password(username, password):
    return ldap.ldap_get_vaild(uid=username, passwd=password)


@auth.verify_password
def verify_password(username, password):
    if ldap_verify_password(username, password):
        return username


@app.route('/auth/ldap')
@auth.login_required
def index():
    return jsonify(authenticated=True, user=auth.current_user())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    pass
