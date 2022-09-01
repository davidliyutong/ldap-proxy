# -*- coding: utf-8 -*-

from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from ldap3.utils.hashed import hashed
from ldap3 import (
    HASHED_SALTED_SHA, MODIFY_REPLACE
)
import json,os
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


def status_code(code):
    return Response(status=code)

# 这里我是通过docker部署服务，这些配置在环境变量传入，你可以根据需要选择直接填写对应值
ldap_host = os.getenv("LDAP_HOST")
port = os.getenv("LDAP_PORT")
base_dn = os.getenv("BASE_DN")
user = os.getenv("BIND_USER")
password = os.getenv("BIND_PASSWORD")
user_dn = os.getenv("USER_DN") # example: uid={0},ou=users,dc=xxxxx,dc=com

app = Flask(__name__)

class LdapUtils(object):
    def __init__(self, ldap_host=None, port=None, base_dn=None, user=None, password=None):
        self.base_dn = base_dn
        try:
            server = Server(ldap_host, port, get_info=ALL)
            self.ldapconn = Connection(server, user=None, password=None,
                                       auto_bind='NONE', version=3, authentication='SIMPLE',
                                       client_strategy='SYNC',
                                       auto_referrals=True, check_names=True, read_only=False, lazy=False,
                                       raise_exceptions=False)
            self.ldapconn.rebind(user=user, password=password)
        except Exception as e:
            print(e)

    def ldap_search_dn(self, uid=None):
        obj = self.ldapconn
        search_base = self.base_dn
        search_scope = SUBTREE
        search_filter = "(cn={0})".format(uid)
        try:
            obj.search(search_base, search_filter, search_scope, attributes=['cn'], paged_size=1)
            if len(obj.response) == 1:
                return obj.response[0]['dn']
            else:
                return None
        except Exception as e:
            print(e)

    def ldap_update_pass(self, uid=None, oldpass=None, newpass=None):
        target_cn = self.ldap_search_dn(uid)
        try:
            hashed_password = hashed(HASHED_SALTED_SHA, newpass)
            print("password:" + hashed_password)
            changes = {
                'userPassword': [(MODIFY_REPLACE, [hashed_password])]
            }
            return self.ldapconn.modify(target_cn, changes=changes)
        except Exception as e:
            print(e)
            return False

    def ldap_get_vaild(self, uid=None, passwd=None):
        if not uid or not passwd:
            return False
        obj = self.ldapconn
        # 这里注意修改成自己ldap上定义的user dn 
        dn = user_dn.format(uid)
        try:
            if obj.rebind(dn, passwd):
                return True
            else:
                return False
        except Exception as e:
            print('e:' + str(e))


ldap = LdapUtils(ldap_host, int(port), base_dn, user,password)  

@app.route('/auth/<user>/<passwd>')
def auth_user(user="user", passwd="passwd"):
    if not ldap.ldap_get_vaild(uid=user,passwd=passwd):
        return status_code(401)
    return jsonify(authenticated=True, user=user)
    
@app.route('/auth/<qop>/<user>/<passwd>')
def auth_qop_user(qop=None, user="user", passwd="passwd"):
    temp = base64.b64decode(passwd.split(" ")[1]).decode()
    if not ldap.ldap_get_vaild(uid=user,passwd=temp.split(":")[1]):
        return status_code(401)
    return jsonify(authenticated=True, user=user)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    auth = request.headers.get('Authorization')
    if auth is not None:
        uid = base64.b64decode(auth.split(" ")[1]).decode().split(":")[0]
        passwd = base64.b64decode(auth.split(" ")[1]).decode().split(":")[1]
        if not ldap.ldap_get_vaild(uid=uid,passwd=passwd):
            return status_code(401)
        return render_template('password.html',uid=uid)
    return status_code(401)

if __name__ == '__main__':
   app.run(host = '0.0.0.0', port = 8080)