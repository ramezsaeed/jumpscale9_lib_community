import shlex

import re
import inspect
import textwrap
from io import StringIO
import collections
from js9 import j
import JumpScale9Lib.clients.agentcontroller.acclient as acclient


STATE_UNKNOWN = 'UNKNOWN'
STATE_SUCCESS = 'SUCCESS'
STATE_TIMEDOUT = 'TIMEOUT'

RESULT_JSON = 20

ResultTuple = collections.namedtuple('ResultTuple', 'status stdout stderr')

JSBASE = j.application.jsbase_get_class()


class ProcessInfo(JSBASE):

    def __init__(self, info):
        JSBASE.__init__(self)
        self._info = info

    @property
    def id(self):
        return self._info['id']

    @property
    def cmd(self):
        return self._info['cmd']

    @property
    def cpu(self):
        return self._info['cpu']

    @property
    def mem(self):
        return self._info['vms']

    def __repr__(self):
        return '<ProcessInfo ID:{this.cmd[id]} CMD:{this.cmd[cmd]}>'.format(this=self)


class Agent(JSBASE):
    """
    Represents an active agent (alive)
    """

    def __init__(self, client, gid, nid, roles):
        JSBASE.__init__(self)
        self._client = client
        self._gid = gid
        self._nid = nid
        self._roles = roles
        self._os_info = None
        self._nic_info = None
        self._aggr_stats = None

    def _get_os_info(self):
        if self._os_info is None:
            self._os_info = self._client.get_os_info(self.gid, self.nid)

        return self._os_info

    def _get_nic_info(self):
        if self._nic_info is None:
            self._nic_info = self._client.get_nic_info(self.gid, self.nid)

        return self._nic_info

    def _get_aggregated_stats(self, update=False):
        if self._aggr_stats is None or update:
            self._aggr_stats = self._client.get_aggregated_stats(
                self.gid, self.nid)

        return self._aggr_stats

    @property
    def gid(self):
        """
        Agent GID
        """
        return self._gid

    @property
    def nid(self):
        """
        Agent NID
        """
        return self._nid

    @property
    def roles(self):
        """
        List of agent roles
        """
        return self._roles or []

    @property
    def hostname(self):
        """
        Gets agent hostname
        """
        return self._get_os_info()['hostname']

    @property
    def cpu(self):
        """
        Gets CPU percentage of agent (with sub processes)
        """
        return self._get_aggregated_stats(True)['cpu']

    @property
    def mem(self):
        """
        Gets the agent VMS (with sub processes)
        """
        return self._get_aggregated_stats(True)['vms']

    @property
    def macaddr(self):
        """
        Gets a dict of interfaces and its hardware addresses
        """
        nics = self._get_nic_info()
        return dict([(nic['name'], nic['hardwareaddr']) for nic in nics])

    @property
    def ipaddr(self):
        """
        Gets a dict of interfaces and its ip addresses
        """
        nics = self._get_nic_info()
        addrr = {}
        for nic in nics:
            nic_addr = [a['addr'] for a in nic['addrs']]
            addrr[nic['name']] = nic_addr

        return addrr

    @property
    def processes(self):
        return list(map(ProcessInfo, self._client.get_processes(self.gid, self.nid)))

    def __repr__(self):
        return '<Agent {this.gid}:{this.nid} {this.roles}>'.format(this=self)


class Result(JSBASE):
    """
    Represents a job result
    """

    def __init__(self, job):
        JSBASE.__init__(self)
        self._job = job

    @property
    def state(self):
        """
        Gets the job exit status (SUCCESS, ERROR, TIMEDOUT)
        """
        return self._job.state

    @property
    def gid(self):
        """
        GID of the agent who returned this result
        """
        return self._job.gid

    @property
    def nid(self):
        """
        NID of the agent who returned this result
        """
        return self._job.nid

    @property
    def result(self):
        """
        The returned object or data (only if state=SUCCESS)
        """
        if self.state != STATE_SUCCESS:
            raise ValueError("Job in %s" % self.state)
        if self._job.level == RESULT_JSON:
            return acclient.jsonLoads(self._job.data)
        return self._job.data

    @property
    def tags(self):
        return self._job.tags

    @property
    def eco(self):
        """
        Any error condition object attached to this job
        """
        critical = self._job.critical
        eco = None

        if critical:
            d = acclient.jsonLoads(critical)
            eco = j.errorhandler.getErrorConditionObject(d)
        elif self.state == STATE_TIMEDOUT:
            eco = j.errorhandler.getErrorConditionObject(
                msg='Timedout waiting for job')
        elif self.state != STATE_SUCCESS:
            eco = j.errorhandler.getErrorConditionObject(
                msg=self._error)

        if eco is not None:
            eco.gid = self.gid
            eco.nid = self.nid

        return eco

    @property
    def _error(self):
        """
        The error message or the process stderr
        """
        if self.state != STATE_SUCCESS:
            return self._job.streams[1] or self._job.data

    # def get_losg(self):

    def __repr__(self):
        return '<Result {this.state} from {this.gid}:{this.nid}>'.format(this=self)


class Peer(JSBASE):
    """
    Represents a peer on a share
    """

    def __init__(self, gid, nid, peer, share):
        JSBASE.__init__(self)
        self._gid = gid
        self._nid = nid
        self._peer = peer
        self._share = share
        self._sync_client = share._sync_client

    @property
    def gid(self):
        """
        GID of that peer
        """
        return self._gid

    @property
    def nid(self):
        """
        NID of that peer
        """
        return self._nid

    @property
    def insync(self):
        """
        Tries to find if this peer is insync with the share. This is not 100%
        reliable because syncthing only detect changes every rescan cycle which
        can take up to a minute.
        """
        need = self._sync_client._get_need(
            self.gid, self.nid, self._share.name)
        if need['progress'] or need['queued'] or need['rest']:
            return False
        else:
            return True

    @property
    def share(self):
        """
        Represents the share object on the peer side
        """
        return self._sync_client.get_share(self.gid, self.nid, self._share.name)

    def __repr__(self):
        return '<Peer {this.gid}:{this.nid}>'.format(this=self)


class Share(JSBASE):
    """
    Represents a shared folder over syncthing
    """

    def __init__(self, gid, nid, folder, sync_client):
        JSBASE.__init__(self)
        self._gid = gid
        self._nid = nid
        self._folder = folder
        self._sync_client = sync_client
        self._ignore = None

    @property
    def gid(self):
        """
        GID of the node
        """
        return self._gid

    @property
    def nid(self):
        """
        NID of the node
        """
        return self._nid

    @property
    def name(self):
        """
        Name (id) of the share
        """
        return self._folder['id']

    @property
    def path(self):
        """
        Path of the local share folder on the node
        """
        return self._folder['path']

    @property
    def peers(self):
        """
        List of peers that are connected to this share.
        """
        peers = self._sync_client._get_devices(self.gid, self.nid)
        share_peers = []
        for share_peer in self._folder['devices']:
            device_id = share_peer['deviceID']
            if device_id not in peers:
                continue

            peer = peers[device_id]
            name = peer['name']
            # name should contain the gid-nid info.
            m = re.match('^(\d+)-(\d+)$', name)
            if not m:
                # not added via the API
                continue

            gid = int(m.group(1))
            nid = int(m.group(2))

            share_peers.append(Peer(gid, nid, peer, self))

        return share_peers

    @property
    def insync(self):
        """
        Tries to find if this peer is insync with the share. This is not 100%
        reliable because syncthing only detect changes every rescan cycle which
        can take up to a minute.
        """
        for peer in self.peers:
            if not peer.insync:
                return False
        return True

    def scan(self, sub=None):
        """"
        Force rescan of share
        """""
        self._sync_client.scan(self.gid, self.nid, self.name, sub)

    @property
    def ignore(self):
        """
        Gets the list of ignored patterns on this share.
        """
        if self._ignore is None:
            self._ignore = self._sync_client._get_ingore(
                self.gid, self.nid, self.path)

        return self._ignore

    def attach(self, gid, nid, path):
        """
        Attach a peer to this share.
        """
        remote_id = self._sync_client._get_id(gid, nid)
        self._sync_client._add_device(
            self.gid, self.nid, '%d-%d' % (gid, nid), remote_id)
        self._sync_client._add_device_to_share(
            self.gid, self.nid, remote_id, self.name)

        self._sync_client.create_share(
            gid, nid, self.name, path, readonly=False)
        local_id = self._sync_client._get_id(self.gid, self.nid)

        self._sync_client._add_device(
            gid, nid, '%d-%d' % (self.gid, self.nid), local_id)
        self._sync_client._add_device_to_share(gid, nid, local_id, self.name)

        share = self._sync_client.get_share(self.gid, self.nid, self.name)
        self._folder = share._folder

    def __repr__(self):
        return '<Share on {this.gid}:{this.nid} {this.path}>'.format(this=self)


class SyncClient(JSBASE):
    API_TIMEOUT = 10

    def __init__(self, client):
        JSBASE.__init__(self)
        self._client = client._client
        self._ids_cache = {}

    def _get_id(self, gid, nid):
        if (gid, nid) in self._ids_cache:
            return self._ids_cache[(gid, nid)]

        runargs = acclient.RunArgs(
            name='get_id', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        id = self._client._load_json_or_die(job)

        self._ids_cache[(gid, nid)] = id
        return id

    def _get_ingore(self, gid, nid, path):
        runargs = acclient.RunArgs(
            name='get_share_ignore', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps({'path': path}))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job).get('ignore', []) or []

    def _get_devices(self, gid, nid):
        runargs = acclient.RunArgs(
            name='list_devices', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        devices = self._client._load_json_or_die(job)
        return dict([(d['deviceID'], d) for d in devices])

    def _get_need(self, gid, nid, folder_id):
        runargs = acclient.RunArgs(
            name='get_share_need', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps({'name': folder_id}))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job)

    def _add_device(self, gid, nid, name, id):
        data = {
            'name': name,
            'id': id
        }

        runargs = acclient.RunArgs(
            name='add_device', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        folder = self._client._load_json_or_die(job)
        return Share(gid, nid, folder, self)

    def _add_device_to_share(self, gid, nid, device_id, folder_id):
        data = {
            'device_id': device_id,
            'folder_id': folder_id
        }

        runargs = acclient.RunArgs(
            name='add_device_to_share', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job)

    def scan(self, gid, nid, name, sub=None):
        """
        Rescan folder

        :param gid: Grid id
        :param nid: Node id
        :param name: Share name
        :param sub: Subfolder to scan in
        :return:
        """
        data = {
            'name': name,
            'sub': sub,
        }

        runargs = acclient.RunArgs(
            name='scan_share', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        self._client._load_json_or_die(job)

    def create_share(self, gid, nid, name, path, readonly=True, ignore=[]):
        """
        Creates a share

        :param gid: Grid id
        :param nid: Node id
        :param name: Share name
        :param path: Share full path on node
        :param readonly: If true this share is master and other peers can't upload to it.
        :param ignore: A list of patterns (files names) to ignore (ex ['**.pyc'])

        :return: a share object
        """
        data = {
            'path': path,
            'readonly': readonly,
            'ignore': ignore,
            'name': name
        }

        runargs = acclient.RunArgs(
            name='create_share', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(
            gid, nid, 'sync', args=runargs, data=j.data.serializer.json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        folder = self._client._load_json_or_die(job)
        return Share(gid, nid, folder, self)

    def list_shares(self, gid, nid):
        """
        List all shares on the node
        """
        runargs = acclient.RunArgs(
            name='list_shares', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return [Share(gid, nid, folder, self) for folder in self._client._load_json_or_die(job)]

    def get_share(self, gid, nid, name):
        """
        Gets a share by name
        """
        shares = self.list_shares(gid, nid)
        for share in shares:
            if share.name == name:
                return share
        raise ValueError('No share with name "%s" found' % name)


# TODO: Currently scheduler has to rebuild command structure for scheduling which is redoing
# work of most of the 'shortcut' methods. We need to restructure this for
# better code reuse.
class SchedulerClient(JSBASE):
    """
    Scheduler interface
    """

    def __init__(self, client):
        JSBASE.__init__(self)
        self._simple = client
        self._client = client._client

    def list(self):
        """
        Lists all scheduled tasks.
        """
        table = dict()
        for item in self._client.schedule_list():
            _id = item.pop('id')
            table[_id] = item
        return table

    def execute(self, id, cron, cmd, path=None, gid=None, nid=None, roles=[], allnodes=True, timeout=5,
                data=None, tags=None):
        """
        Schedule execution of command according to cron

        Cron expression represents a set of times, using 6 space-separated fields.

        +--------------+------------+-----------------+----------------------------+
        | Field name   | Mandatory? | Allowed values  | Allowed special characters |
        +==============+============+=================+============================+
        | Seconds      | Yes        | 0-59            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Minutes      | Yes        | 0-59            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Hours        | Yes        | 0-23            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Day of month | Yes        | 1-31            | * / , - ?                  |
        +--------------+------------+-----------------+----------------------------+
        | Month        | Yes        | 1-12 or JAN-DEC | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Day of week  | Yes        | 0-6 or SUN-SAT  | * / , - ?                  |
        +--------------+------------+-----------------+----------------------------+

        Note: Month and Day-of-week field values are case insensitive. "SUN", "Sun", and "sun" are equally accepted.

        :param id: Cron job id, must be unique globally and can be used later to stop the schedule
        :param cron: Cron string to run the task
        """
        parts = shlex.split(cmd)
        assert len(parts) > 0, "Empty command string"
        cmd = parts[0]
        args = parts[1:]

        nid, roles, fanout = self._simple._get_route(nid, roles, allnodes)

        runargs = acclient.RunArgs(
            max_time=timeout, working_dir=path, name=cmd, args=args)
        return self._client.schedule_add(id=id, cron=cron, gid=gid, nid=nid, cmd=acclient.CMD_EXECUTE,
                                         args=runargs, roles=roles, fanout=fanout, data=data, tags=tags)

    def executeBash(self, id, cron, cmds, path=None, gid=None, nid=None, roles=[], allnodes=True, timeout=5, tags=None):
        """
        Schedule bash script execution according to given cron.

        Cron expression represents a set of times, using 6 space-separated fields.

        +--------------+------------+-----------------+----------------------------+
        | Field name   | Mandatory? | Allowed values  | Allowed special characters |
        +==============+============+=================+============================+
        | Seconds      | Yes        | 0-59            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Minutes      | Yes        | 0-59            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Hours        | Yes        | 0-23            | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Day of month | Yes        | 1-31            | * / , - ?                  |
        +--------------+------------+-----------------+----------------------------+
        | Month        | Yes        | 1-12 or JAN-DEC | * / , -                    |
        +--------------+------------+-----------------+----------------------------+
        | Day of week  | Yes        | 0-6 or SUN-SAT  | * / , - ?                  |
        +--------------+------------+-----------------+----------------------------+

        Note: Month and Day-of-week field values are case insensitive. "SUN", "Sun", and "sun" are equally accepted.

        :param id: Cron job id, must be unique globally and can be used later to stop the schedule
        :param cron: Cron string to run the task
        """
        nid, roles, fanout = self._simple._get_route(nid, roles, allnodes)

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        return self._client.schedule_add(id, cron, gid=gid, nid=nid, cmd='bash',
                                         args=runargs, roles=roles, fanout=fanout, data=cmds, tags=tags)

    def executeJumpscript(self, id, cron, domain=None, name=None, content=None, path=None, method=None,
                          gid=None, nid=None, roles=[], allnodes=True, timeout=5, args={}, tags=None):
        nid, roles, fanout = self._simple._get_route(nid, roles, allnodes)

        if domain is not None:
            assert name is not None, "name is required in case 'domain' is given"
        else:
            if not content and not path and not method:
                raise ValueError(
                    'domain/name, content, or path must be supplied')

        runargs = acclient.RunArgs(max_time=timeout)
        if domain is not None:
            runargs = runargs.update({'domain': domain, 'name': name})
            return self._client.schedule_add(
                id,
                cron,
                gid=gid,
                nid=nid,
                cmd=acclient.CMD_EXECUTE_JUMPSCRIPT,
                args=runargs,
                data=j.data.serializer.json.dumps(args),
                roles=roles,
                fanout=fanout,
                tags=tags)
        else:
            # call the unexposed jumpscript_content extension manually
            if method:
                content = self._simple._getFuncCode(method)
            elif path:
                content = j.sal.fs.fileGetContents(path)

            data = {
                'content': content,
                'args': args,
            }

            return self._client.schedule_add(
                id,
                cron,
                gid=gid,
                nid=nid,
                cmd=acclient.CMD_EXECUTE_JUMPSCRIPT_CONTENT,
                args=runargs,
                data=j.data.serializer.json.dumps(data),
                roles=roles,
                fanout=fanout,
                tags=tags)

    def unschedule(self, id):
        """
        Unschedule a task given it's ID

        You can get a list of all scheduled ID's using the :func:`simple.SchedulerClient.list` method.
        :param id: id of the job to unschedule
        """
        return self._client.schedule_remove(id)

    def unschedule_prefix(self, prefix):
        """
        Unschedule all tasks that its ID is starting with prefix

        You can get a list of all scheduled ID's using the :func:`simple.SchedulerClient.list` method.
        :param prefix: prefix of the cron ID to unschedule
        """
        return self._client.schedule_remove_prefix(prefix)


class SimpleClient(JSBASE):
    """
    Simple client
    """

    def __init__(self, advanced_client):
        JSBASE.__init__(self)
        self._client = advanced_client
        self._sync = SyncClient(self)
        self._scheduler = SchedulerClient(self)

    @property
    def sync(self):
        return self._sync

    @property
    def scheduler(self):
        return self._scheduler

    def getAgents(self):
        """
        Gets a list of all active agents
        """
        cmd = self._client.cmd(None, None, 'controller', acclient.RunArgs(
            name='list_agents'), roles=['*'])
        job = cmd.get_next_result()

        agents = self._client._load_json_or_die(job)
        results = []
        for key, roles in agents.items():
            gid, _, nid = key.partition(':')
            results.append(Agent(self._client, int(gid), int(nid), roles))

        return results

    def _build_result(self, results):
        buff = StringIO()
        for gid, nid, state, stdout, stderr in results:
            buff.write('$agent (%d,%d)\n' % (gid, nid))
            buff.write(stdout)
            buff.write('\n')
            if state != STATE_SUCCESS:
                buff.write('##RC: %s\n' % state)
                buff.write('##ERROR:\n%s\n' % stderr)

            buff.write(
                '#######################################################\n\n')
        return buff.getvalue()

    def _process_exec_jobs(self, execjobs, die, timeout, fanout):
        jobs = []
        for job in execjobs:
            state = STATE_UNKNOWN
            try:
                job.wait(timeout)
                state = job.state
            except acclient.ResultTimeout:
                if die:
                    raise
                state = STATE_TIMEDOUT

            stdout, stderr = job.streams
            error = stderr or job.data
            if state != STATE_SUCCESS and die:
                raise acclient.AgentException(
                    'Job on agent {job.gid}.{job.nid} failed with status: "{job.state}" and message: "{error}"'.format(
                        job=job, error=error)
                )

            jobs.append((job.gid, job.nid, state, stdout, error))

        if fanout:
            # potential multiple results.
            return self._build_result(jobs)
        else:
            # single job
            _, _, state, stdout, stderr = jobs.pop()
            return ResultTuple(state, stdout, stderr)

    def _get_route(self, nid, roles, fanout):
        if nid is None and not roles:
            roles = ['*']
        elif nid is not None:
            fanout = False

        return nid, roles, fanout

    def executeAsync(self, cmd, path=None, gid=None, nid=None, roles=[], allnodes=True, timeout=5,
                     data=None, tags=None):
        """
        Executes a command on node(s)

        :param cmd: Command to execute ex('ls -l /opt')
        :param path: CWD of commnad (where to execute)
        :param gid: GID of node
        :param nid: NID of node
        :param roles: List of agent roles to match (only agent that satisfies all the given roles will execue this)
        :param allnodes: Execute on ALL agents that matches the roles (default True), if False only one agent will
                       execute
        :param timeout: Process timeout, if took more than `timeout` the process will get killed and error is returned.
        :param data: raw data that will be feed to command stdin.
        :param tags: Tags string that will be attached to the command and return with the results as is. Usefule to
                   attach meta data to the command for analysis
        """

        parts = shlex.split(cmd)
        assert len(parts) > 0, "Empty command string"
        cmd = parts[0]
        args = parts[1:]

        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        command = self._client.execute(gid, nid, cmd, cmdargs=args, args=runargs, data=data,
                                       roles=roles, fanout=fanout, tags=tags)

        return list(command.get_jobs().values())

    def execute(self, cmd, path=None, gid=None, nid=None, roles=[], allnodes=True, die=True, timeout=5,
                data=None, tags=None):
        """
        Executes a command on node(s)

        :param cmd: Command to execute ex('ls -l /opt')
        :param path: CWD of commnad (where to execute)
        :param gid: GID of node
        :param nid: NID of node
        :param roles: List of agent roles to match (only agent that satisfies all the given roles will execue this)
        :param allnodes: Execute on ALL agents that matches the roles (default True), if False only one agent will
                       execute
        :param die: If True raises an exception when error occure, otherwise return results with error state.
        :param timeout: Process timeout, if took more than `timeout` the process will get killed and error is returned.
        :param data: raw data that will be feed to command stdin.
        :param tags: Tags string that will be attached to the command and return with the results as is. Usefule to
                   attach meta data to the command for analysis
        """
        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        jobs = self.executeAsync(cmd, path=path, gid=gid, nid=nid, roles=roles,
                                 allnodes=fanout, timeout=timeout, data=data, tags=tags)
        return self._process_exec_jobs(jobs, die, timeout, fanout)

    def executeBashAsync(self, cmds, path=None, gid=None, nid=None, roles=[], allnodes=True, timeout=5, tags=None):
        """
        Same as execute but cmds can be a bash script
        """
        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        command = self._client.cmd(
            gid, nid, 'bash', args=runargs, data=cmds, roles=roles, fanout=fanout, tags=tags)

        return list(command.get_jobs().values())

    def executeBash(self, cmds, path=None, gid=None, nid=None, roles=[], allnodes=True, die=True, timeout=5, tags=None):
        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        jobs = self.executeBashAsync(cmds=cmds, path=path, gid=gid, nid=nid, roles=roles,
                                     allnodes=fanout, timeout=timeout, tags=tags)
        return self._process_exec_jobs(jobs, die, timeout, fanout)

    def _getFuncCode(self, func):
        if not inspect.isfunction(func):
            raise ValueError('method must be function (not class method)')

        source = inspect.getsource(func)
        source = textwrap.dedent(source)
        if func.__name__ != 'action':
            source = re.sub('^def\s+%s\s*\(' %
                            func.__name__, 'def action(', source, 1)
        return source

    def executeJumpscript(self, domain=None, name=None, content=None, path=None, method=None,
                          gid=None, nid=None, roles=[], allnodes=True, die=True, timeout=5, args={}, tags=None):
        """
        Executes jumpscript synchronusly and immediately get resutls

        :param domain: jumpscript domain name
        :param name: jumpscript name. Note when using domain/name to execute jumpscript the script
                   is loaded from the node jumpscritps folder.
        :param content: Optional jumpscript content (as code) to execute.
        :param path: Optional full path to jumpscript on node to execute
        :param method: A python function to execute.
        :param gid: GID of node
        :param nid: NID of node
        :param roles: List of agent roles to match (only agent that satisfies all the given roles will execue this)
        :param allnodes: Execute on ALL agents that matches the roles (default True), if False only one agent will
                       execute
        :param die: If True raises an exception when error occure, otherwise return results with error state.
        :param timeout: Process timeout, if took more than `timeout` the process will get killed and error is returned.
        :param args: Arguments to jumpscript
        :param tags: Tags string that will be attached to the command and return with the results as is. Usefule to
                   attach meta data to the command for analysis
        """
        jobs = self.executeJumpscriptAsync(
            domain=domain, name=name, content=content, path=path, method=method,
            gid=gid, nid=nid, roles=roles, allnodes=allnodes, timeout=timeout, args=args, tags=tags
        )

        results = []
        for job in jobs:
            state = STATE_UNKNOWN
            try:
                job.wait(timeout)
            except acclient.ResultTimeout:
                if die:
                    raise
                job._jobdata['state'] = STATE_TIMEDOUT

            state = job.state

            if state != STATE_SUCCESS and die:
                r = Result(job)
                raise r.eco

            results.append(Result(job))

        return results

    def executeJumpscriptAsync(self, domain=None, name=None, content=None, path=None, method=None,
                               gid=None, nid=None, roles=[], allnodes=True, timeout=5, args={}, tags=None):
        """
        Executes jumpscript asynchronusly and immediately return jobs

        :param domain: jumpscript domain name
        :param name: jumpscript name. Note when using domain/name to execute jumpscript the script
                   is loaded from the node jumpscritps folder.
        :param content: Optional jumpscript content (as code) to execute.
        :param path: Optional full path to jumpscript on node to execute
        :param method: A python function to execute.
        :param gid: GID of node
        :param nid: NID of node
        :param roles: List of agent roles to match (only agent that satisfies all the given roles will execue this)
        :param allnodes: Execute on ALL agents that matches the roles (default True), if False only one agent will
                       execute
        :param timeout: Process timeout, if took more than `timeout` the process will get killed and error is returned.
        :param args: Arguments to jumpscript
        :param tags: Tags string that will be attached to the command and return with the results as is. Usefule to
                   attach meta data to the command for analysis
        """
        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        if domain is not None:
            assert name is not None, "name is required in case 'domain' is given"
        else:
            if not content and not path and not method:
                raise ValueError(
                    'domain/name, content, or path must be supplied')

        runargs = acclient.RunArgs(max_time=timeout)
        if domain is not None:
            command = self._client.execute_jumpscript(gid=gid, nid=nid, domain=domain, name=name,
                                                      args=args, runargs=runargs, roles=roles, fanout=fanout, tags=tags)
        else:
            # call the unexposed jumpscript_content extension manually
            if method:
                content = self._getFuncCode(method)
            elif path:
                content = j.sal.fs.fileGetContents(path)

            command = self._client.execute_jumpscript_content(
                gid, nid, content, args=args, runargs=runargs, roles=roles, fanout=fanout, tags=tags
            )

        return list(command.get_jobs().values())

    def reboot(self, gid=None, nid=None, roles=[], allnodes=True):
        """
        Same as execute but cmds can be a bash script
        """
        nid, roles, fanout = self._get_route(nid, roles, allnodes)

        runargs = acclient.RunArgs()
        command = self._client.cmd(
            gid, nid, 'reboot', args=runargs, roles=roles, fanout=fanout)

        return list(command.get_jobs().keys())

    def tunnel_create(self, gid, nid, local, remote_gid, remote_nid, ip, remote):
        """
        Opens a tunnel that accepts connection at the agent's local port `local`
        and forwards the received connections to remote agent `gateway` which will
        forward the tunnel connection to `ip:remote`

        Note: The agent will proxy the connection over the agent-controller it recieved this open command from.

        :param gid: Grid id
        :param nid: Node id
        :param local: Agent's local listening port for the tunnel. 0 for dynamic allocation
        :param remote_gid: Grid id of remote node
        :param remote_nid: Node id of remote node
        :param ip: The endpoint ip address on the remote agent network. Note that IP must be a real ip not a host name
                 dns names lookup is not supported.
        :param remote: The endpoint port on the remote agent network
        """

        agents = self.getAgents()
        found = False
        for agent in agents:
            if agent.nid == remote_nid and agent.gid == remote_gid:
                found = True
                break

        if not found:
            raise acclient.AgentException(
                'Remote end %s:%s is not alive!' % (remote_gid, remote_nid))

        gateway = '%s.%s' % (remote_gid, remote_nid)
        return self._client.tunnel_open(gid, nid, local, gateway, ip, remote)

    def tunnel_close(self, gid, nid, local, remote_gid, remote_nid, ip, remote):
        """
        Closes a tunnel previously opened by tunnel_open. The `local` port MUST match the
        real open port returned by the tunnel_open function. Otherwise the agent will not match the tunnel and return
        ignore your call.

        Closing a non-existing tunnel is not an error.
        """
        gateway = '%s.%s' % (remote_gid, remote_nid)
        return self._client.tunnel_close(gid, nid, local, gateway, ip, remote)

    def tunnel_list(self, gid, nid):
        """
        Return all opened connection that are open from the agent over the agent-controller it
        received this command from
        """
        return self._client.tunnel_list(gid, nid)
