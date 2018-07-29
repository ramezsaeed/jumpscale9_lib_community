
from js9 import j

import capnp

import zernoNetConfigModel_capnp as ZeroNetConfigModel

# class ZeroNetConfigDBFactory():
#
#     def get(self, name):
#         return AtYourServiceDB(name)
JSBASE = j.application.jsbase_get_class()


class ZeroNetConfigDB(JSBASE):

    def __init__(self, category):
        self.db = j.data.kvs.getRedisStore("0netconfig", changelog=False)
        JSBASE.__init__(self)

    def set(self, key, obj):
        from IPython import embed
        self.logger.debug("DEBUG NOW set")
        embed()

    def get(self, key):
        from IPython import embed
        self.logger.debug("DEBUG NOW set")
        embed()

    def delete(self, key):
        from IPython import embed
        self.logger.debug("DEBUG NOW set")
        embed()
