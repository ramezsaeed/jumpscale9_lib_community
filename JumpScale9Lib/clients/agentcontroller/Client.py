import JumpScale9Lib.clients.agentcontroller.acclient as acclient
import JumpScale9Lib.clients.agentcontroller.simple as simple
from js9 import j

JSConfigFactory = j.tools.configmanager.base_class_configs
JSConfigClient = j.tools.configmanager.base_class_config

TEMPLATE = """
address = "localhost"
port = 6379
password_ = ""
"""
JSBASE = j.application.jsbase_get_class()


class ACFactory(JSConfigFactory):

    def __init__(self):
        self.__jslocation__ = "j.clients.agentcontroller"
        JSConfigFactory.__init__(self, ACClient)

    def getRunArgs(self, domain=None, name=None, max_time=0, max_restart=0, recurring_period=0, stats_interval=0,
                   args=None, loglevels='*', loglevels_db=None, loglevels_ac=None, queue=None):
        """
        Creates a reusable run arguments object

        :domain: Domain name
        :name: script or executable name
        :max_time: Max run time, 0 (forever), -1 forever but remember during reboots (long running),
            other values is timeout
        :max_restart: Max number of restarts if process died in under 5 min.
        :recurring_period: Scheduling time
        :stats_interval: How frequent the stats aggregation is done/flushed to AC
        :args: Command line arguments (in case of execute)
        :loglevels: Which log levels to capture and pass to logger
        :loglevels_db: Which log levels to store in DB (overrides logger defaults)
        :loglevels_ac: Which log levels to send to AC (overrides logger defaults)
        """
        return acclient.RunArgs(domain=domain, name=name, max_time=max_time, max_restart=max_restart,
                                recurring_period=recurring_period, stats_interval=stats_interval, args=args,
                                loglevels=loglevels, loglevels_db=loglevels_db, loglevels_ac=loglevels_ac,
                                queue=queue)


class ACClient(JSConfigClient, simple.SimpleClient):
    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigClient.__init__(self, instance=instance,
                                data=data, parent=parent, template=TEMPLATE, interactive=interactive)
        c = self.config.data
        self.address = c['address']
        self.port = c['port']
        self.password = c['password_']
        self._advanced_client = None
        simple.SimpleClient.__init__(self.advanced_client)

    @property
    def advanced_client(self):
        if not self._advanced_client:
            self._advanced_client = acclient.Client(address=self.address, port=self.port, password=self.password)

        return self._advanced_client
