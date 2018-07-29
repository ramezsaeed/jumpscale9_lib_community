import requests
import base64
from JumpScale9Lib.clients.whmcs import phpserialize

SSL_VERIFY = False

from js9 import j

JSBASE = j.application.jsbase_get_class()


class whmcsusers(JSBASE):

    def __init__(self, authenticationparams, url):
        JSBASE.__init__(self)
        self.authenticationparams = authenticationparams
        self.url = url

    def _call_whmcs_api(self, requestparams):
        actualrequestparams = dict()
        actualrequestparams.update(requestparams)
        actualrequestparams.update(self.authenticationparams)
        response = requests.post(
            self.url, data=actualrequestparams, verify=SSL_VERIFY)
        return response

    def create_user(self, name, company, emails, password, companyurl, displayname, creationTime):
        self.logger.debug(('Creating %s' % name))
        create_user_request_params = dict(

            action='addclient',
            responsetype='json',
            firstname=name,
            lastname="",
            companyname=company,
            email=emails,
            password2=password,
            country="unknown",
            currency="1",
            customfields=base64.b64encode(phpserialize.dumps(
                [companyurl, displayname, creationTime])),
            noemail=True,
            skipvalidation=True

        )

        response = self._call_whmcs_api(create_user_request_params)
        return response.ok

    def update_user(self, name, company, emails, password, companyurl, displayname, creationTime):
        self.logger.debug(('Updating %s' % name))
        user_request_params = dict(

            action='updateclient',
            responsetype='json',
            firstname=name,
            companyname=company,
            email=emails,
            password2=password,
            customfields=base64.b64encode(phpserialize.dumps(
                [companyurl, displayname, creationTime])),
            noemail=True,
            skipvalidation=True

        )

        response = self._call_whmcs_api(user_request_params)
        return response.ok

    def list_users(self):
        result_users = {}
        list_users_request_params = dict(
            action='getclients',
            limitnum=10000000,
            responsetype='json'
        )

        response = self._call_whmcs_api(list_users_request_params)
        if response.ok:
            users = response.json()
            if users['numreturned'] > 0:
                for u in users['clients']['client']:
                    result_users[u['firstname']] = u
            return result_users
        else:
            raise

    def delete_user(self, userid):
        delete_users_request_params = dict(
            action='deleteclient',
            clientid=userid,
            responsetype='json'
        )

        response = self._call_whmcs_api(delete_users_request_params)
        return response.ok

    def add_credit(self, userid, description, amount):
        add_credit_request_params = dict(
            action='addcredit',
            clientid=userid,
            description=description,
            amount=amount,
            responsetype='json'
        )
        response = self._call_whmcs_api(add_credit_request_params)
        return response.ok

    def add_debit(self, userid):
        pass
