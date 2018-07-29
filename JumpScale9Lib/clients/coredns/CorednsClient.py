from js9 import j
import json

JSConfigBase = j.tools.configmanager.base_class_config

TEMPLATE = """
redisconfigname = ""
"""

class CorednsClient(JSConfigBase):
    """
    info about plugin redis: 
        https://coredns.io/explugins/redis/
    """
    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigBase.__init__(self, instance=instance,
                              data=data, parent=parent, template=TEMPLATE)
        self._redis_client = None
    
    @property
    def redis_config(self):
        """
        redis which is the connection to the redis backend of coredns
        """
        if self._redis_client is None:
            self._redis_client = j.clients.redis_config.get(
                instance=self.config.data["redisconfigname"])
        return self._redis_client

    @property
    def redis_client(self):
        """
        redis which is the connection to the redis backend of coredns
        """
        return self.redis_config.redis

    def _get_parts(self,dns):
        subdomain = dns.split(".")[0]
        host = ".".join(dns.split(".")[1:])
        return subdomain,host


    def _add_record(self, domain, record, override=False):
        subdomain, host = self._get_parts(domain)

        if not host.endswith('.'):
            host = host + '.'

        exist = self.redis_client.hget(host, subdomain)

        if not exist or override:
            self.redis_client.hset(host, subdomain, record)

    def register_a_record(self, domain, ip4, ttl=360, override=False):
        record = {
            "a":[{
                "ip": ip4,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)

    def register_aaaa_record(self, domain, ip6, ttl=360, override=False):
        record ={
            "aaaa":[{
                "ip": ip6,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)

    def register_cname_record(self, domain, host, ttl=360, override=False):
        record ={
            "cname":[{
                "host": host,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)

    def register_ns_record(self, domain, host, ttl=360, override=False):
        record ={
            "ns":[{
                "host": host,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)
    
    def register_text_record(self, domain, text, ttl=360, override=False):
        record ={
            "text":[{
                "host": text,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)
    
    def register_mx_record(self, domain, host, preference, ttl=360, override=False):
        record ={
            "mx":[{
                "host": host,
                "preference": preference,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)
    
    def register_srv_record(self, domain, priority, weight, port, target, ttl=360, override=False):
        record ={
            "srv":[{
                "priority": priority,
                "weight": weight,
                "port": port,
                "target": target,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)
    
    def register_soa_record(self, domain, ns, mbox, refresh, retry, expire, minttl, ttl=360, override=False):
        record ={
            "soa":[{
                "ns": ns,
                "MBox": mbox,
                "refresh": refresh,
                "retry": retry,
                "expire": expire,
                "ttl": ttl
            }]
        }
        self._add_record(domain, json.dumps(record), override=override)
    
    def unregister(self, domain):
        subdomain, host = self._get_parts(domain)
        if not host.endswith('.'):
            host = host + '.'
        self.redis_client.hdel(host, subdomain)