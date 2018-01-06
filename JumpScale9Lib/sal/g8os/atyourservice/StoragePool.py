from JumpScale9Lib.sal.g8os.abstracts import AYSable
from JumpScale9Lib.sal.g8os.StoragePool import StoragePool
from JumpScale9Lib.sal.g8os.StoragePool import FileSystem
from JumpScale9Lib.sal.g8os.StoragePool import Snapshot


class StoragePoolAys(AYSable):

    def __init__(self, storagepool):
        self._obj = storagepool
        self.actor = 'storagepool'

    def create(self, aysrepo):
        actor = aysrepo.actorGet(self.actor)
        args = {
            'metadataProfile': self._obj.fsinfo['metadata']['profile'],
            'dataProfile': self._obj.fsinfo['data']['profile'],
            'devices': self._obj.devices,
            'node': self._node_name,
        }
        return actor.serviceCreate(instance=self._obj.name, args=args)

    @property
    def _node_name(self):
        for nic in self._obj.node.client.info.nic():
            for addr in nic['addrs']:
                if addr['addr'].split('/')[0] == self._obj.node.addr:
                    return nic['hardwareaddr'].replace(':', '')
        raise AttributeError("name not find for node {}".format(self._obj.node))


class FileSystemAys(AYSable):

    def __init__(self, filesystem):
        self._obj = filesystem
        self.actor = 'filesystem'

    def create(self, aysrepo):
        actor = aysrepo.actorGet(self.actor)
        args = {
            'storagePool': self._obj.pool.name,
            'name': self._obj.name,
            # 'readOnly': ,FIXME
            # 'quota': ,FIXME
        }
        return actor.serviceCreate(instance=self._obj.name, args=args)


if __name__ == '__main__':
    from js9 import j
    j.atyourservice.server._start()
    repo = j.atyourservice.server.aysRepos.get('/opt/code/cockpit_repos/grid')
    node1 = j.sal.g8os.get_node('172.20.0.91')
    node2 = j.sal.g8os.get_node('172.20.0.92')
    cluster = j.sal.g8os.create_storagecluster('cluster1', [node1, node2], 'hdd', 8, True)
    from IPython import embed
    embed()
