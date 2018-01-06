from .IPMIMachine import IPMIMachine
from js9 import j


class MachineFactory:
    """Machine sal."""

    def __init__(self):
        self.__jslocation__ = "j.sal.machine"
        self.logger = j.logger.get("j.sal.machine")

    def get_ipmi(self, ip, login, passwd, prefab=None):
        """
        Get an IPMI Server.

        @param ip str: ip of the ipmi interface.
        @param login str: the username to login to ipmi.
        @param passwd str: the password to login to ipmi.
        @param prefab prefab: prefab object to where the ipmi command will be executed.
        """
        prefab = prefab or j.tools.prefab.local
        return IPMIMachine(ip, login, passwd, prefab=prefab)
