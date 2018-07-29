from .GogsClient import GogsClient
from js9 import j

JSConfigBaseFactory = j.tools.configmanager.base_class_configs


class GogsFactory(JSConfigBaseFactory):

    def __init__(self):
        self.__jslocation__ = "j.clients.gogs"
        self.__imports__ = "requests,psycopg2"
        JSConfigBaseFactory.__init__(self, GogsClient)
