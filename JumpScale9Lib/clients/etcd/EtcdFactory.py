from js9 import j
from .EtcdClient import EtcdClient


JSConfigFactoryBase = j.tools.configmanager.base_class_configs


class EtcdFactory(JSConfigFactoryBase):

    def __init__(self):
        self.__jslocation__ = "j.clients.etcd"
        super().__init__(child_class=EtcdClient)
