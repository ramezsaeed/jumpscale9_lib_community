import requests
import base64
from JumpScale9Lib.clients.whmcs import phpserialize

SSL_VERIFY = False

from js9 import j

JSBASE = j.application.jsbase_get_class()


class whmcsorders(JSBASE):

    def __init__(self, authenticationparams, url):
        JSBASE.__init__(self)
        self._authenticationparams = authenticationparams
        self._url = url

    def _call_whmcs_api(self, requestparams):
        actualrequestparams = dict()
        actualrequestparams.update(requestparams)
        actualrequestparams.update(self._authenticationparams)
        response = requests.post(
            self._url, data=actualrequestparams, verify=SSL_VERIFY)
        return response

    def add_order(self, userId, productId, name, cloudbrokerId, status='Active'):

        request_params = dict(

            action='addorder',
            name=name,
            status=status,
            pid=productId,
            clientid=userId,
            billingcycle='monthly',
            paymentmethod='paypal',
            customfields=base64.b64encode(phpserialize.dumps([cloudbrokerId])),
            noemail=True,
            skipvalidation=True

        )

        response = self._call_whmcs_api(request_params)
        return response.ok

    def list_orders(self):

        request_params = dict(
            action='getorders',
            limitnum=10000000,
            responsetype='json'
        )

        response = self._call_whmcs_api(request_params)
        if response.ok:
            orders = response.json()
            if orders['numreturned'] > 0:
                return orders['orders']['order']
            return []
        else:
            raise

    def delete_order(self, orderId):
        request_params = dict(
            action='deleteorder',
            orderid=orderId,
            responsetype='json'
        )

        response = self._call_whmcs_api(request_params)
        return response.ok
