from js9 import j
from .MatrixClient import MatrixClient

JSConfigBaseFactory = j.tools.configmanager.base_class_configs


class MatrixFactory(JSConfigBaseFactory):
    def __init__(self):
        JSConfigBaseFactory.__init__(self, MatrixClient)
        self.__jslocation__ = "j.clients.matrix"

    @staticmethod
    def install():
        j.sal.process.execute("pip3 install matrix_client")
