#!/usr/bin/env python
from js9 import j
import os

JSBASE = j.application.jsbase_get_class()


class AysFsFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.sal.aysfs"
        JSBASE.__init__(self)

    def get(self, name, prefab=None):
        return AysFs(name=name, prefab=prefab)

    def _getFlist(self, name):
        if not j.sal.fs.exists('/aysfs/flist/'):
            j.sal.fs.createDir('/aysfs/flist/')

        flist = '/aysfs/flist/%s.flist' % name
        if not j.sal.fs.exists(flist):
            self.logger.debug('[+] downloading flist: %s' % name)
            storx = j.clients.storx.get('https://stor.JumpScale9Lib.org/storx')
            storx.getStaticFile('%s.flist' % name, flist)

    def getJumpscale(self, prefab=None):
        self._getFlist('js8_opt')

        js8opt = AysFs('jumpscale', prefab)
        js8opt.setUnique()
        js8opt.addMount('/aysfs/docker/jumpscale', 'RO',
                        '/aysfs/flist/js8_opt.flist', prefix='/opt')
        js8opt.addBackend('/ays/backend/jumpscale', 'js8_opt')
        js8opt.addStor()
        return js8opt

    def getOptvar(self, prefab=None):
        self._getFlist('js8_optvar')

        js8optvar = AysFs('optvar', prefab)
        js8optvar.addMount('/aysfs/docker/$NAME', 'OL',
                           '/aysfs/flist/js8_optvar.flist', prefix='/optvar')
        js8optvar.addBackend('/ays/backend/$NAME', 'js8_optvar')
        js8optvar.addStor()
        return js8optvar


class AysFs(JSBASE):

    def __init__(self, name, prefab=None):
        JSBASE.__init__(self)
        self._prefab = prefab
        if self._prefab is None:
            self._prefab = j.tools.prefab.local

        self.mounts = []
        self.backends = []
        self.stors = []

        self.root = '/aysfs'
        self.name = name.replace('/', '-')
        self.unique = False
        self.tmux = self._prefab.system.tmux

        self.defstor = 'https://stor.JumpScale9Lib.org/storx'

    def setRoot(self, root):
        self.root = root

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name.replace('/', '-')

    def setUnique(self, value=True):
        self.unique = value

    def isUnique(self):
        return self.unique

    def getPrefixs(self):
        prefixs = {}

        for mount in self.mounts:
            source = '%s/%s' % (mount['path'], mount['prefix'])
            prefixs[source] = mount['prefix']

        return prefixs

    def getConfig(self):
        return '%s/etc/%s.toml' % (self.root, self.name)

    def loadConfig(self):
        config_path = self.getConfig()

        if not j.sal.fs.exists(config_path):
            return False

        cfg = j.data.serializer.toml.load(config_path)

        for mount in cfg['mount']:
            self.addMount(mount['path'], mount['mode'],
                          mount['flist'], mount['backend'])

        for name, backend in cfg['backend'].items():
            self.addBackend(backend['path'], backend[
                            'namespace'], backend['stor'], name=name)

        for name, store in cfg['aydostor'].items():
            self.addStor(remote=store['addr'], username=store[
                         'login'], password=store['passwd'], name=name)

        return True

    def addMount(self, path, mode, flist=None, backend='default', prefix=''):
        mount = {
            'path': path,
            'backend': backend,
            'mode': mode,
            'prefix': prefix
        }

        if flist:
            mount['flist'] = flist

        self.mounts.append(mount)

        return True

    def addBackend(self, path, namespace, stor='default', name='default'):
        backend = {
            'name': name,
            'path': path,
            'stor': stor,
            'namespace': namespace,
            'encrypted': False,                # FIXME
            'aydostor_push_cron': '@every 10s'  # FIXME
        }

        self.backends.append(backend)

        return True

    def addStor(self, remote=None, username='', password='', name='default'):
        stor = {
            'name': name,
            'addr': remote if remote else self.defstor,
            'login': username,
            'passwd': password
        }

        self.stors.append(stor)

        return True

    def _generate(self, items):
        build = {}

        # extract name from item and use it as key
        for item in items:
            temp = item.copy()
            temp.pop('name', None)

            build[item['name']] = temp

        return build

    def _clean(self, items):
        output = []

        for item in items:
            temp = item.copy()
            temp.pop('prefix', None)

            output.append(temp)

        return output

    def _parse(self, items):
        for item in items:
            if item.get('path'):
                item['path'] = item['path'].replace('$NAME', self.name)

        return items

    def generate(self):
        config = {
            'mount': self._clean(self.mounts),
            'backend': self._generate(self.backends),
            'aydostor': self._generate(self.stors)
        }

        return j.data.serializer.toml.dumps(config)

    def unmount(self, path):
        self._prefab.core.run('umount %s; exit 0' % path)

    def _ensure_path(self, path):
        if not j.sal.fs.exists(path):
            j.sal.fs.createDir(path)

    def _install(self):
        self._ensure_path(self.root)
        self._ensure_path('%s/etc' % self.root)
        self._ensure_path('%s/bin' % self.root)

        binary = '%s/bin/aysfs' % self.root

        if not j.sal.fs.exists(binary):
            self.logger.debug('[+] downloading aysfs binary')
            storx = j.clients.storx.get('https://stor.JumpScale9Lib.org/storx')
            storx.getStaticFile('aysfs', binary)
            j.sal.fs.chmod(binary, 0o755)

    def start(self):
        # ensure that all required path and binaries exists
        self._install()

        # parsing paths (replaces names)
        self._parse(self.mounts)
        self._parse(self.backends)

        self.logger.debug('[+] preparing mountpoints')
        for mount in self.mounts:
            # force umount (cannot stat folder if Transport endpoint is not
            # connected)
            self.unmount(mount['path'])

            if not j.sal.fs.exists(mount['path']):
                j.sal.fs.createDir(mount['path'])

        self.logger.debug('[+] checking backends')
        for backend in self.backends:
            if not j.sal.fs.exists(backend['path']):
                j.sal.fs.createDir(backend['path'])

        self.logger.debug('[+] writing config file')
        config = self.getConfig()
        j.sal.fs.writeFile(config, self.generate())

        self.logger.debug('[+] starting aysfs')

        cmdline = '%s/bin/aysfs -config %s' % (self.root, config)
        self.tmux.executeInScreen('aysfs', config, cmdline)

        return True

    def stop(self):
        config_path = self.getConfig()
        self.tmux.killWindow('aysfs', config_path)

        for mount in self.mounts:
            # force umount (cannot stat folder if Transport endpoint is not
            # connected)
            self.unmount(mount['path'])

    def isRunning(self):
        config = self.getConfig()

        # if window doesn't exists, we can stop now
        if not self.tmux.windowExists('aysfs', config):
            return False

        # checking if the process on the window is aysfs or does it died
        parent = j.sal.process.getProcessObject(
            self.tmux.getPid('aysfs', self.getConfig()))

        # if no children, nothing is running
        if len(parent.children()) == 0:
            return False

        for child in parent.children():
            # we got it
            if child.name() == 'aysfs':
                return True

        return False
