from jumpscale import j
from JumpscaleLib.sal.g8os.Disk import Disks, DiskType
from JumpscaleLib.sal.g8os.StoragePool import StoragePools
from collections import namedtuple


Mount = namedtuple('Mount', ['device', 'mountpoint', 'fstype', 'options'])


class Node:
    """Represent a G8OS Server"""

    def __init__(self, addr, port=6379, password=None):
        # g8os client to talk to the node
        self._client = j.clients.g8core.get(host=addr, port=port, password=password)
        self.addr = addr
        self.port = port
        self.disks = Disks(self)
        self.storagepools = StoragePools(self)

    @classmethod
    def from_ays(cls, service):
        return cls(
            addr=service.model.data.redisAddr,
            port=service.model.data.redisPort,
            password=service.model.data.redisPassword
        )

    @property
    def client(self):
        return self._client

    def _eligible_fscache_disk(self, disks):
        """
        return the first disk that is eligible to be used as filesystem cache
        First try to find a SSH disk, otherwise return a HDD
        """
        # Pick up the first ssd
        usedisks = []
        for pool in (self._client.btrfs.list() or []):
            for device in pool['devices']:
                usedisks.append(device['path'])
        for disk in disks[::-1]:
            if disk.devicename in usedisks:
                disks.remove(disk)
                continue
            if disk.type in [DiskType.ssd, DiskType.nvme]:
                return disk
            elif disk.type == DiskType.cdrom:
                disks.remove(disk)
            if len(disk.partitions) > 0:
                disks.remove(disk)
        # If no SSD found, pick up the first disk
        return disks[0]

    def _mount_fscache(self, storagepool):
        """
        mount the fscache storage pool and copy the content of the in memmory fs inside
        """
        if storagepool.mountpoint != '/var/cache/containers':
            storagepool.umount()

        if not storagepool.mountpoint:
            storagepool.mount('/var/cache/containers')
            self.client.bash('rm -fr /var/cache/containers/*')

    def ensure_persistance(self, name='fscache'):
        """
        look for a disk not used,
        create a partition and mount it to be used as cache for the g8ufs
        set the label `fs_cache` to the partition
        """
        disks = self.disks.list()
        if len(disks) <= 0:
            # if no disks, we can't do anything
            return

        # check if there is already a storage pool with the fs_cache label
        fscache_sp = None
        for sp in self.storagepools.list():
            if sp.name == name:
                fscache_sp = sp
                break

        # create the storage pool if we don't have one yet
        if fscache_sp is None:
            disk = self._eligible_fscache_disk(disks)
            fscache_sp = self.storagepools.create(
                name,
                devices=[
                    disk.devicename],
                metadata_profile='single',
                data_profile='single',
                overwrite=True)

        # mount the storage pool
        self._mount_fscache(fscache_sp)
        return fscache_sp

    def list_mounts(self):
        allmounts = []
        for mount in self.client.info.disk():
            allmounts.append(Mount(mount['device'],
                                   mount['mountpoint'],
                                   mount['fstype'],
                                   mount['opts']))
        return allmounts

    def __str__(self):
        return "Node <{host}:{port}>".format(
            host=self.addr,
            port=self.port,
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        a = "{}:{}".format(self.addr, self.port)
        b = "{}:{}".format(other.addr, other.port)
        return a == b

    def __hash__(self):
        return hash((self.addr, self.port))
