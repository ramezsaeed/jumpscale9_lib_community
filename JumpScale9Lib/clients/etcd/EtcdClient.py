import socket

import gevent.socket

import etcd3
from js9 import j

JSConfigClientBase = j.tools.configmanager.base_class_config


if socket.socket is gevent.socket.socket:
    # this is needed when running from within 0-robot
    import grpc.experimental.gevent
    grpc.experimental.gevent.init_gevent()

_template = """
host = "127.0.0.1"
port = 2379
#timeout = null
user = ""
password = ""
"""


class EtcdClient(JSConfigClientBase):

    def __init__(self, instance="main", data=None, parent=None, template=None, ui=None, interactive=True):
        data = data or {}
        super().__init__(instance=instance, data=data, parent=parent, template=_template, ui=ui, interactive=interactive)
        self._api = None

    @property
    def api(self):
        if self._api is None:
            data = self.config.data
            kwargs = {
                'host': data['host'],
                'port': data['port'],
            }
            if data['user'] and data['password']:
                kwargs.update({
                    'user': data['user'],
                    'passwrod': data['password']
                })
            self._api = etcd3.client(**kwargs)
            print("client created")
        return self._api
