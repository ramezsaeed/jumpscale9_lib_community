from js9 import j
import netifaces


class DHCP:
    """
Configure DHCP on a certain network (interface) by giving a range of IP addresses
 which will be issued to clients booting up on the given network interface
    """

    def __init__(self):
        self.__jslocation__ = "j.sal.dhcp_ihc"
        self.__imports__ = "netifaces"
        self.configPath = j.tools.path.get(
            '/etc').joinpath('dhcp3', 'dhcpd.conf')
        self._executor = j.tools.executorLocal

    def configure(self, ipFrom, ipTo, interface):
        interface = netifaces.ifaddresses(interface)[2]
        if self.configPath.exists():
            header = '''default-lease-time 600;
max-lease-time 7200;
'''
            self.configPath.touch()
            self.configPath.write_text(header)

        config = '''
subnet %s netmask %s {
    option subnet-mask 255.255.255.0;
    option routers 10.0.0.1;
    range %s %s;
}''' % (interface['addr'], interface['netmask'], ipFrom, ipTo)

        self.configPath.write_text(config, append=True)
        self.restart()

    def start(self):
        """
        Start DHCP server.
        """
        self._executor.execute('service isc-dhcp-server start')

    def stop(self):
        """
        Stop DHCP server.
        """
        self._executor.execute('service isc-dhcp-server stop')

    def restart(self):
        """Restarts DHCP server"""
        self._executor.execute('service isc-dhcp-server restart')
