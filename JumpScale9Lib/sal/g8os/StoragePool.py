from JumpScale9Lib.sal.g8os.abstracts import Mountable
from JumpScale9Lib.sal.g8os.abstracts import AYSable
import os


class StoragePools:
    def __init__(self, node):
        self.node = node
        self._client = node._client

    def list(self):
        storagepools = []
        btrfs_list = self._client.btrfs.list()
        if btrfs_list:
            for btrfs in self._client.btrfs.list():
                if btrfs['label'].startswith('sp_'):
                    name = btrfs['label'].split('_', 1)[1]
                    devicenames = [device['path'] for device in btrfs['devices']]
                    storagepools.append(StoragePool(self.node, name, devicenames))
        return storagepools

    def get(self, name):
        for pool in self.list():
            if pool.name == name:
                return pool
        raise ValueError("Could not find StoragePool with name {}".format(name))

    def create(self, name, devices, metadata_profile, data_profile, overwrite=False):
        label = 'sp_{}'.format(name)
        self._client.btrfs.create(label, devices, metadata_profile, data_profile, overwrite=overwrite)
        pool = StoragePool(self.node, name, devices)
        return pool


class StoragePool(Mountable):
    def __init__(self, node, name, devices):
        self.node = node
        self._client = node._client
        self.devices = devices
        self.name = name
        self._mountpoint = None
        self._ays = None

    @property
    def devicename(self):
        return 'UUID={}'.format(self.uuid)

    def mount(self, target=None):
        if target is None:
            target = os.path.join('/mnt/storagepools/{}'.format(self.name))
        return super().mount(target)

    def delete(self, zero=True):
        """
        Destroy storage pool
        param name: name of storagepool to delete
        param zero: write zeros (nulls) to the first 500MB of each disk in this storagepool
        """
        if self.mountpoint:
            self.umount()
        if zero:
            for device in self.devices:
                self._client.system('dd if=/dev/zero bs=1M count=500 of={}'.format(device))

    @property
    def mountpoint(self):
        for device in self.devices:
            mountpoint = self._client.disk.getinfo(device[5:]).get('mountpoint')
            if mountpoint:
                return mountpoint

    def device_add(self, *devices):
        self._client.btrfs.device_add(self._get_mountpoint(), *devices)

    def device_remove(self, *devices):
        self._client.btrfs.device_remove(self._get_mountpoint(), *devices)

    @property
    def fsinfo(self):
        return self._client.btrfs.info(self.mountpoint)

    @mountpoint.setter
    def mountpoint(self, value):
        # do not do anything mountpoint is dynamic
        return

    def _get_mountpoint(self):
        mountpoint = self.mountpoint
        if not mountpoint:
            raise RuntimeError("Can not perform action when filesystem is not mounted")
        return mountpoint

    @property
    def info(self):
        for fs in self._client.btrfs.list():
            if fs['label'] == 'sp_{}'.format(self.name):
                return fs
        return None

    def raw_list(self):
        mountpoint = self._get_mountpoint()
        return self._client.btrfs.subvol_list(mountpoint) or []

    def list(self):
        subvolumes = []
        for subvol in self.raw_list():
            path = subvol['Path']
            type_, _, name = path.partition('/')
            if type_ == 'filesystems':
                subvolumes.append(FileSystem(name, self))
        return subvolumes

    def get(self, name):
        """
        Get Filesystem
        """
        for filesystem in self.list():
            if filesystem.name == name:
                return filesystem
        raise ValueError("Could not find filesystem with name {}".format(name))

    def exists(self, name):
        """
        Check if filesystem with name exists
        """
        for subvolume in self.list():
            if subvolume.name == name:
                return True
        return False

    def create(self, name, quota=None):
        """
        Create filesystem
        """
        mountpoint = self._get_mountpoint()
        fspath = os.path.join(mountpoint, 'filesystems')
        self._client.filesystem.mkdir(fspath)
        subvolpath = os.path.join(fspath, name)
        self._client.btrfs.subvol_create(subvolpath)
        if quota:
            pass
        return FileSystem(name, self)

    @property
    def size(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs['devices']:
                total += device['size']
        return total

    @property
    def uuid(self):
        fs = self.info
        if fs:
            return fs['uuid']
        return None

    @property
    def used(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs['devices']:
                total += device['used']
        return total

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale9Lib.sal.g8os.atyourservice.StoragePool import StoragePoolAys
            self._ays = StoragePoolAys(self)
        return self._ays

    def __repr__(self):
        return "StoragePool <{}>".format(self.name)


class FileSystem:
    def __init__(self, name, pool):
        self.name = name
        self.pool = pool
        self._client = pool.node.client
        self.path = os.path.join(self.pool.mountpoint, 'filesystems', name)
        self.snapshotspath = os.path.join(self.pool.mountpoint, 'snapshots', self.name)
        self._ays = None

    def delete(self, includesnapshots=True):
        """
        Delete filesystem
        """
        self._client.btrfs.subvol_delete(self.path)
        if includesnapshots:
            for snapshot in self.list():
                snapshot.delete()
            self._client.filesystem.remove(self.snapshotspath)

    def get(self, name):
        """
        Get snapshot
        """
        for snap in self.list():
            if snap.name == name:
                return snap
        raise ValueError("Could not find snapshot {}".format(name))

    def list(self):
        """
        List snapshots
        """
        snapshots = []
        if self._client.filesystem.exists(self.snapshotspath):
            for fileentry in self._client.filesystem.list(self.snapshotspath):
                if fileentry['is_dir']:
                    snapshots.append(Snapshot(fileentry['name'], self))
        return snapshots

    def exists(self, name):
        """
        Check if a snapshot exists
        """
        return name in self.list()

    def create(self, name):
        """
        Create snapshot
        """
        snapshot = Snapshot(name, self)
        if self.exists(name):
            raise RuntimeError("Snapshot path {} exists.")
        self._client.filesystem.mkdir(self.snapshotspath)
        self._client.btrfs.subvol_snapshot(self.path, snapshot.path)
        return snapshot

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale9Lib.sal.g8os.atyourservice.StoragePool import FileSystemAys
            self._ays = FileSystemAys(self)
        return self._ays

    def __repr__(self):
        return "FileSystem <{}: {!r}>".format(self.name, self.pool)


class Snapshot:
    def __init__(self, name, filesystem):
        self.filesystem = filesystem
        self._client = filesystem.pool.node.client
        self.name = name
        self.path = os.path.join(self.filesystem.snapshotspath, name)

    def rollback(self):
        self.filesystem.delete(False)
        self._client.btrfs.subvol_snapshot(self.path, self.filesystem.path)

    def delete(self):
        self._client.btrfs.subvol_delete(self.path)

    def __repr__(self):
        return "Snapshot <{}: {!r}>".format(self.name, self.filesystem)
