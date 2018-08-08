from jumpscale import j

import erppeek


JSConfigFactory = j.tools.configmanager.base_class_configs
JSConfigClient = j.tools.configmanager.base_class_config

TEMPLATE = """
url = ""
db = ""
username = ""
password_ = ""
"""


class ErppeekFactory(JSConfigFactory):

    def __init__(self):
        self.__jslocation__ = "j.clients.erppeek"
        self.__imports__ = "erppeek"
        JSConfigFactory.__init__(self, Erppeek)


class Erppeek(JSConfigClient):

    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigClient.__init__(self, instance=instance,
                                data=data, parent=parent, template=TEMPLATE, interactive=interactive)
        self.logger = j.logger.get("j.clients.erppeek")
        self._client = erppeek.Client(self.config.data["url"], self.config.data["db"],
                                      self.config.data["username"], self.config.data["password_"])

    def config_check(self):
        """
        check the configuration if not what you want the class will barf & show you where it went wrong
        """
        if not self.config.data["url"] or not self.config.data["db"] \
                or not self.config.data["username"] or not self.config.data["password_"]:
            return "url, db, username and password_ are not properly configured, cannot be empty"

    def count_records(self, model, domain=None):
        """
        count the records in model :model that matches domain
        :param model: name of the model
        :param domain: search domain
        :return: number of records
        """
        return self._client.model(model).count(domain)

    def create_record(self, model, data):
        """
        create a new record
        :param model: model name
        :param data: data of the record
        :return: a Record class
        """
        return self._client.model(model).create(data)
