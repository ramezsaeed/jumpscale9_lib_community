
from js9 import j

from JumpScale9Lib.clients.whmcs.whmcsusers import whmcsusers
from JumpScale9Lib.clients.whmcs.whmcstickets import whmcstickets
from JumpScale9Lib.clients.whmcs.whmcsorders import whmcsorders

JSConfigClient = j.tools.configmanager.base_class_config

TEMPLATE = """
username = ""
md5_password_ = ""
accesskey_ = ""
url = ""
cloudspace_product_id = ""
operations_user_id = ""
operations_department_id = ""
"""
class WhmcsInstance(JSConfigClient):

    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigClient.__init__(self, instance=instance,
                                data=data, parent=parent, template=TEMPLATE, interactive=interactive)

        c = self.config.data
        self._username = c['username']
        self._md5_password = c['md5_password_']
        self._accesskey = c['accesskey_']
        self._url = c['url']
        self._cloudspace_product_id = c['cloudspace_product_id']
        self._operations_user_id = c['operations_user_id']
        self._operations_department_id = c['operations_department_id']

        self._whmcsusers = None
        self._whmcstickets = None
        self._whmcsorders = None

    @property
    def users(self):
        authenticationparams = {
            'username': self._username,
            'password': self._md5_password,
            'accesskey': self._accesskey}

        if not self._whmcsusers:
            self._whmcsusers = whmcsusers(authenticationparams, self._url)
        return self._whmcsusers

    @property
    def tickets(self):
        authenticationparams = {
            'username': self._username,
            'password': self._md5_password,
            'accesskey': self._accesskey}

        if not self._whmcstickets:
            self._whmcstickets = whmcstickets(authenticationparams,
                                              self._url,
                                              self._operations_user_id,
                                              self._operations_department_id)
        return self._whmcstickets

    @property
    def orders(self):
        authenticationparams = {
            'username': self._username,
            'password': self._md5_password,
            'accesskey': self._accesskey}

        if not self._whmcsorders:
            self._whmcsorders = whmcsorders(authenticationparams, self._url)
        return self._whmcsorders
