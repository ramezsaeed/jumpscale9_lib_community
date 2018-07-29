import os

from js9 import j

from .FlaskServer import FlaskServer

JSConfigBase = j.tools.configmanager.base_class_configs


class GedisFactory(JSConfigBase):

    def __init__(self):
        self.__jslocation__ = "j.servers.flask"

        JSConfigBase.__init__(self, FlaskServer)


    def configure(
            self,
            instance="main",
            port=8889,
            host="localhost",
            secret="",
            apps_dir="",
    ):
        data = {
            "port": port,
            "host": host,
            "secret_": secret,
            "apps_dir":apps_dir,
        }

        return self.get(instance, data)

    def cmds_get(self,namespace,capnpbin):
        """
        Used in client only
        """
        return GedisCmds(namespace=namespace,capnpbin=capnpbin)

    @property
    def template_engine(self):
        if self._template_engine is None:
            from jinja2 import Environment, PackageLoader

            self._template_engine = Environment(
                loader=PackageLoader('JumpScale9Lib.servers.gedis2', 'templates'),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return self._template_engine

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))

    @property
    def code_server_template(self):
        if self._template_code_server is None:
            self._template_code_server = self.template_engine.get_template("template.py")
        return self._template_code_server

    @property
    def code_model_template(self):
        if self._code_model_template is None:
            self._code_model_template = self.template_engine.get_template("ModelBase.py")
        return self._code_model_template        

    @property
    def code_start_template(self):
        if self._code_start_template is None:
            self._code_start_template = self.template_engine.get_template("start.py")
        return self._code_start_template

    @property
    def code_test_template(self):
        if self._code_test_template is None:
            self._code_test_template = self.template_engine.get_template("test.py")
        return self._code_test_template
