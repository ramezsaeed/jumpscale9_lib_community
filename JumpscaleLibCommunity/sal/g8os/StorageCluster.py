from jumpscale import j
from JumpscaleLib.sal.g8os.Disk import DiskType
from JumpscaleLib.sal.g8os.Container import Container
from JumpscaleLib.sal.g8os.ARDB import ARDB
from JumpscaleLib.sal.g8os.Node import Node
import io
import time


class StorageCluster:
    """StorageCluster is a cluster of ardb servers"""

    def __init__(self, label):
        """
        @param label: string repsenting the name of the storage cluster
        """
        self.label = label
        self.name = label
        self.nodes = []
        self.filesystems = []
        self.storage_servers = []
        self.disk_type = None
        self.has_slave = None
        self._ays = None

    @classmethod
    def from_ays(cls, service):
        cluster = cls(label=service.name)
        cluster.disk_type = str(service.model.data.diskType)
        cluster.has_slave = service.model.data.hasSlave

        for ardb_service in service.producers.get('ardb', []):
            storages_server = StorageServer.from_ays(ardb_service)
            cluster.storage_servers.append(storages_server)
            if storages_server.node not in cluster.nodes:
                cluster.nodes.append(storages_server.node)

        return cluster

    @property
    def nr_server(self):
        """
        Number of storage server part of this cluster
        """
        return len(self.storage_servers)

    def create(self, nodes, disk_type, nr_server, has_slave=True):
        """
        @param nodes: list of node on wich we can deploy storage server
        @param disk_type: type of disk to be used by the storage server
        @param nr_server: number of storage server to deploy
        @param has_slave: boolean specifying of we need to deploy slave storage server
        """
        self.nodes = nodes
        if disk_type not in DiskType.__members__.keys():
            raise TypeError("disk_type should be on of {}".format(', '.join(DiskType.__members__.keys())))
        self.disk_type = disk_type
        self.has_slave = has_slave

        for disk in self._find_available_disks():
            self.filesystems.append(self._prepare_disk(disk))

        nr_filesystems = len(self.filesystems)

        def get_filesystem(i, exclude_node=None):
            fs = self.filesystems[i % (nr_filesystems - 1)]
            while exclude_node is not None and fs.pool.node == exclude_node:
                i += 1
                fs = self.filesystems[i % (nr_filesystems - 1)]
            return fs

        port = 2000
        for i in range(nr_server):
            fs = get_filesystem(i)
            bind = "0.0.0.0:{}".format(port)
            port = port + 1
            storage_server = StorageServer(cluster=self)
            storage_server.create(filesystem=fs, name="{}_{}".format(self.name, i), bind=bind)
            self.storage_servers.append(storage_server)

        if has_slave:
            for i in range(nr_server):
                storage_server = self.storage_servers[i]
                fs = get_filesystem(i, storage_server.node)
                bind = "0.0.0.0:{}".format(port)
                port = port + 1
                slave_server = StorageServer(cluster=self)
                slave_server.create(
                    filesystem=fs,
                    name="{}_{}".format(
                        self.name,
                        (nr_server + i)),
                    bind=bind,
                    master=storage_server)
                self.storage_servers.append(slave_server)

    def _find_available_disks(self):
        """
        return a list of disk that are not used by storage pool
        or has a different type as the one required for this cluster
        """
        available_disks = []
        for node in self.nodes:
            available_disks.extend(node.disks.list())

        cluster_name = 'sp_cluster_{}'.format(self.label)
        usedisks = []
        for node in self.nodes:
            for disk in node.disks.list():
                # skip devices which have filesystems with other labels
                if len(disk.filesystems) > 0 and not disk.filesystems[0]['label'].startswith(cluster_name):
                    usedisks.append(disk)
                # skip devices which have partitions
                if len(disk.partitions) > 0:
                    usedisks.append(disk)

        for disk in available_disks:
            if disk in usedisks:
                available_disks.remove(disk)
                continue
            if disk.type.name != self.disk_type:
                available_disks.remove(disk)
                continue
        return available_disks

    def _prepare_disk(self, disk):
        """
        _prepare_disk make sure a storage pool and filesytem are present on the disk.
        returns the filesytem created
        """
        name = "cluster_{}_{}".format(self.label, disk.name)

        try:
            pool = disk.node.storagepools.get(name)
        except ValueError:
            pool = disk.node.storagepools.create(name, [disk.devicename], 'single', 'single', overwrite=True)

        pool.mount()
        try:
            fs = pool.get(name)
        except ValueError:
            fs = pool.create(name)

        return fs

    def start(self):
        for server in self.storage_servers:
            server.start()

    def stop(self):
        for server in self.storage_servers:
            server.stop()

    def is_running(self):
        # TODO: Improve this, what about part of server running and part stopped
        for server in self.storage_servers:
            if not server.is_running():
                return False
        return True

    def health(self):
        """
        Return a view of the state all storage server running in this cluster
        example :
        {
        'cluster1_1': {'ardb': True, 'container': True, 'slaveof': None},
        'cluster1_2': {'ardb': True, 'container': True, 'slaveof': None},
        }
        """
        health = {}
        for server in self.storage_servers:
            running, _ = server.ardb.is_running()
            health[server.name] = {
                'ardb': running,
                'container': server.container.is_running(),
                'slaveof': server.master.name if server.master else None,
            }
        return health

    @property
    def ays(self):
        if self._ays is None:
            from JumpscaleLib.sal.g8os.atyourservice.StorageCluster import StorageClusterAys
            self._ays = StorageClusterAys(self)
        return self._ays

    def __repr__(self):
        return "StorageCluster <{}>".format(self.label)


class StorageServer:
    """ardb servers"""

    def __init__(self, cluster):
        self.cluster = cluster
        self.container = None
        self.ardb = None
        self.master = None

    def create(self, filesystem, name, bind='0.0.0.0:16739', master=None):
        self.master = master
        self.container = Container(
            name=name,
            node=filesystem.pool.node,
            flist="https://hub.gig.tech/gig-official-apps/ardb-rocksdb.flist",
            filesystems={filesystem: '/mnt/data'},
            host_network=True,
        )
        self.ardb = ARDB(
            name=name,
            container=self.container,
            bind=bind,
            data_dir='/mnt/data/{}'.format(name),
            master=master.ardb if master else None
        )

    @classmethod
    def from_ays(cls, ardb_services):
        ardb = ARDB.from_ays(ardb_services)
        container = Container.from_ays(ardb_services.parent)
        storage_server = cls(None)
        storage_server.container = container
        storage_server.ardb = ardb
        if ardb.master:
            storage_server.master = cls(None)
            storage_server.master.container = ardb.master.container
            storage_server.master.ardb = ardb.master
        return storage_server

    @property
    def name(self):
        if self.ardb:
            return self.ardb.name
        return None

    @property
    def node(self):
        if self.container:
            return self.container.node
        return None

    def _find_port(self, start_port=2000):
        while True:
            if j.sal.nettools.tcpPortConnectionTest(self.node.addr, start_port, timeout=2):
                start_port += 1
                continue
            return start_port

    def start(self, timeout=30):
        if self.master:
            self.master.start()

        if not self.container.is_running():
            self.container.start()

        _, port = self.ardb.bind.split(":")
        self.ardb.bind = '0.0.0.0:{}'.format(self._find_port(port))
        self.ardb.start(timeout=timeout)

    def stop(self, timeout=30):
        self.ardb.stop(timeout=timeout)
        self.container.stop()

    def is_running(self):
        container = self.container.is_running()
        ardb, _ = self.ardb.is_running()
        return (container and ardb)
