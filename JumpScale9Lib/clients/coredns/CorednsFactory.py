from js9 import j

JSConfigBase = j.tools.configmanager.base_class_configs

from .CorednsClient import CorednsClient

class CorednsFactory(JSConfigBase):

    def __init__(self):
        self.__jslocation__ = "j.clients.coredns"
        JSConfigBase.__init__(self, CorednsClient)

    def get_by_params(self, instance="main", redisname="coredns"):
        """
        name of redis connection
        get as follows:

        j.clients.redis_config.get_by_params(instance='coredns', ipaddr='localhost', port=6380, password='', unixsocket='', ardb_patch=False)

        """
        data = {}
        data["redisconfigname"] = redisname
        return self.get(instance=instance, data=data)

    def test(self, instance="coredns"):
        redis = j.clients.redis_config.get(instance=instance)
        cl = self.get_by_params(redis.instance)
        domain = 'clienttest.a.grid.tf.'
        ip = "195.134.212.32"
        cl.register_a_record(domain, ip)

        assert ip == j.tools.dnstools.getNameRecordIPs(domain)[0]
        cl.unregister(domain)
        print("Success")
