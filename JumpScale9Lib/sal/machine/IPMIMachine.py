from js9 import j
from .Machine import Machine


class IPMIMachine(Machine):
    """IPMI Machine."""

    def __init__(self, ip, login, passwd, prefab):
        """
        IPMI Machine.

        @param ip str: ip of the ipmi interface.
        @param login str: the username to login to ipmi.
        @param passwd str: the password to login to ipmi.
        @param prefab prefab: prefab object to where the ipmi command will be executed.
        """
        self.ip = ip
        self.login = login
        self.passwd = passwd
        self.logger = j.logger.get('j.sal.machine.ipmi')

        self._prefab = prefab
        self._executor = self._prefab._executor

    def ipmi(self, commands):
        """Send an ipmi command to the machine."""
        return self._prefab.core.run('ipmitool -I lanplus -H %s -U %s -P %s %s'
                                      % (self.ip, self.login, self.passwd, commands))

    def poweron(self):
        """Power on the machine."""
        return self.ipmi('chassis power on')

    def poweroff(self):
        """Power off the machine."""
        return self.ipmi('chassis power off')

    def reboot(self):
        """Reboot the machine."""
        return self.ipmi('chassis power cycle')

    def enablepxe_once(self):
        """Enable boot from pxe on the next reboot."""
        return self.ipmi('chassis bootdev pxe')
