
from js9 import j
# from JumpScale9Lib.tools.develop.DevelopTools import DebugSSHNode


class GCC:

    def __init__(self):
        super(GCC, self).__init__()
        self.__jslocation__ = "j.tools.gcc"

    def get(self, nodes=[]):
        """
        define which nodes to init,
        format = ["localhost", "ovh4", "anode:2222", "192.168.6.5:23"]
        this will be remembered in local redis for further usage
        if node = [], previously defined node will be used

        make sure nodes have your SSH key authorized before using there
        can do this with
        j.tools.gcc.authorizeNode(addr,passwd,keyname,login="root",port=22)

        """
        return GCC_Mgmt(nodes)

    def authorizeNode(self, addr, passwd, keyname, login="root", port=22):
        j.tools.executor.getSSHBased(addr=addr, port=port, login=login, passwd=passwd,
                                     debug=False, checkok=True, allow_agent=True, look_for_keys=True, pushkey=keyname)


class GCC_Mgmt():

    def __init__(self, nodes=[]):
        if len(nodes) > 0:
            self.init(nodes=nodes)

        self._host_nodes = []
        self._docker_nodes = []
        self.dns_domain = None
        self._basicAuth = None

    def _parseNode(self, nodes):
        nodesObjs = []
        for item in nodes.split(","):
            if item.find(":") != -1:
                addr, sshport = item.split(":")
                addr = addr.strip()
                sshport = int(sshport)
            else:
                addr = item.strip()
                sshport = 22 if addr != "localhost" else 0
            nodesObjs.append(DebugSSHNode(addr, sshport))
        return nodesObjs

    def init(self, nodes=[], domain="", login=None, passwd=None):
        """
        nodes : define which nodes to init,
            format = ["localhost", "ovh4", "anode:2222", "192.168.6.5:23"]
            this will be remembered in local redis for further usage
        domain: define for which domain the skydns cluster is Authoritative
        login : login to protect etcd cluster
        passwd : passwd to protect etcd cluster
        """
        if not j.data.types.list.check(nodes):
            nodes = [nodes]
        j.core.db.set("gcc.host_nodes", ','.join(nodes))
        self.dns_domain = domain
        if login and passwd:
            self._basicAuth = {'login': login, 'passwd': passwd}

    @property
    def host_nodes(self):
        """
        node object that represent the host machines
        """
        if self._docker_nodes == []:
            if j.core.db.get("gcc.host_nodes") is None:
                self.init()
            nodes = j.core.db.get("gcc.host_nodes").decode()
            self._host_nodes = self._parseNode(nodes)
        return self._host_nodes

    @property
    def docker_nodes(self):
        """
        node object that represent the docker container where all
        the acutal apps are installed
        """
        if self._docker_nodes == []:
            if j.core.db.get("gcc.docker_nodes") is None:
                self.init()
            nodes = j.core.db.get("gcc.docker_nodes").decode()
            self._docker_nodes = self._parseNode(nodes)
        return self._docker_nodes

    def install(self, pubkey, force=False):
        """
        pubkey, public ssh key to authorize inside the dockers deployed on the host.
        """
        containers = []
        for i, node in enumerate(self.host_nodes):
            weave_peer = self.host_nodes[0].addr if i > 0 else None
            print("Prepare host %s" % node.addr)
            self._installHostApp(node, weave_peer, force=force)

            print("Create docker container on %s" % node.addr)
            name = 'gcc-%s' % (i + 1)
            ssh_port = node.prefab.docker.ubuntu(name, ports="80:80 443:443 53/udp:54", pubkey=pubkey, force=force)
            containers.append("%s:%s" % (node.addr, ssh_port))

            # needed cause weave already listen on port 53 on the host
            _, ip, _ = node.prefab.core.run("jsdocker getip -n %s" % name)
            node.prefab.core.run(
                "iptables -t nat -A PREROUTING -i eth0 -p udp --dport 53 -j DNAT --to-destination %s:53" %
                ip, action=True)

        j.core.db.set("gcc.docker_nodes", ','.join(containers))

        print('All host nodes ready.')
        print('Start installations dockers')
        for i, node in enumerate(self.docker_nodes):
            self._installDockerApps(node, force=force)

    def _installHostApp(self, node, weave_peer, force=False):
        node.prefab.development.js8.install()
        node.prefab.installer.docker(force=force)
        node.prefab.apps.weave.build(start=True, peer=weave_peer, force=force)

    def _installDockerApps(self, node, force=False):
        node.prefab.development.js8.install()

        peers = ["http://%s" % node.addr for node in self.docker_nodes]
        node.prefab.apps.etcd.build(start=True, host="http://%s" % node.addr, peers=peers, force=force)
        node.prefab.apps.skydns.build(start=True, force=force)
        node.prefab.apps.aydostore(start=True, addr='127.0.0.1:8090', backend="$VARDIR/aydostor", force=force)
        # node.prefab.apps.agentcontroller(start=True, force=force)
        node.prefab.apps.caddy.build(ssl=True, start=True, dns=node.addr, force=force)
        self._configCaddy(node)
        self._configSkydns(node)

    def _configCaddy(self, node):
        cfg = node.prefab.core.file_read("$JSCFGDIR/caddy/caddyfile.conf")
        cfg += """
        proxy /etcd localhost:2379 localhost:4001 {
        without /etcd
        }

        proxy /storex localhost:8090 {
        without /storex
        }
        """

        if self._basicAuth:
            cfg += "\nbasicauth /etcd %s %s\n" % (self._basicAuth['login'], self._basicAuth['passwd'])
        cfg = node.prefab.core.file_write("$JSCFGDIR/caddy/caddyfile.conf", cfg)
        node.prefab.processmanager.ensure('caddy')

    def _configSkydns(self, node):
        if self._basicAuth:
            skydnsCl = j.clients.skydns.get(node.addr, self._basicAuth['login'], self._basicAuth['passwd'])
        else:
            skydnsCl = j.clients.skydns.get(node.addr)
        print(skydnsCl.setConfig({'dns_addr': '0.0.0.0:53', 'domain': self.domain}))
        node.prefab.processmanager.ensure('skydns')

    def healthcheck(self):
        """
        """
        # TODO: *3 implement some healthchecks done over agentcontrollers
        #- check diskpace
        #- check cpu
        #- check that 3 are there
        #- check that weave network is intact
        #- check sycnthing is up to date
        #- port checks ...

    def nameserver(self, login, passwd):
        """
        credentials to etcd to allow management of DNS records
        """
        return GCC_Nameserver(self, login, passwd)

    def aydostor(self, login, passwd):
        return GCC_aydostor(self, login, passwd)


class GCC_Nameserver():
    """
    define easy to use interface on top of nameserver management
    """

    def __init__(self, manager, login, passwd):
        self.manager = manager
        self.login = login
        self.passwd = passwd

    def ns_addHost(self, hostname, target):
        """
        set a record (A, AAAA, CNAME) which point from hostname -> target (hello.exemple.com -> 8.8.8.8)
        """
        host = self.manager.host_nodes[0].addr
        skydns = j.clients.skydns.get('https://%s/etcd' % host, self.login, self.passwd)
        skydns.setRecordA(hostname, target)


class GCC_aydostor():
    """
    define easy to use interface on top of aydostor (use aydostor client, needs to be separate client in js8)
    """

    def __init__(self, manager, login, passwd):
        self.manager = manager
        self.login = login
        self.passwd = passwd

    def ns_addHost(addr, dnsinfo):  # to be further defined
        pass
        # TODO: use https over caddy to speak to etcd to configure skydns
