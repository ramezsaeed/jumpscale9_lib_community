# from __future__ import print_function
from js9 import j

JSConfigFactory = j.tools.configmanager.base_class_configs
JSConfigClient = j.tools.configmanager.base_class_config
JSBASE = j.application.jsbase_get_class()
TEMPLATE = """
url = "redis://localhost:6379/0"
actors_path = "actors"
"""


class CeleryFactory(JSConfigFactory, JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.clients.celery"
        JSBASE.__init__(self)
        JSConfigFactory.__init__(self, CeleryClient)

    def test(self):
        """
        js9 'j.clients.celery.test()'
        """
        cmd="js9 'c=j.clients.celery.get();c.flower_start()'"
        j.tools.tmux.execute(cmd, session='main', window='flower',pane='main', session_reset=False, window_reset=True)
        print("celery flower running on http://localhost:5555/")






class CeleryClient(JSConfigClient, JSBASE):

    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSBASE.__init__(self)
        JSConfigClient.__init__(self, instance=instance,
                                data=data, parent=parent, template=TEMPLATE, interactive=interactive)
        self.actors = {}
        self.app = None
        self.url = self.config.data['url']
        self.actorsPath = self.config.data['actors_path']

    def flower_start(self):
        """
        js9 'c=j.clients.celery.get();c.flower_start()'
        """
        from flower.command import FlowerCommand
        from flower.utils import bugreport

        flower = FlowerCommand()

        argv = ['flower.py', '--broker=%s' % self.url]

        flower.execute_from_commandline(argv=argv)

    def _getCode(self, path):
        state = "start"
        C = j.sal.fs.fileGetContents(path)
        basename = j.sal.fs.getBaseName(path)
        name = basename.replace(".py", "").lower()
        out = "class %s():\n" % name
        for line in C.split("\n"):
            # if state=="method":
            #     if line.strip().find("def")==0:

            if state == "class":
                # now processing the methods
                if line.strip().find("def") == 0:
                    # state=="method"
                    pre = line.split("(", 1)[0]
                    pre = pre.replace("def ", "")
                    method_name = pre.strip()
                    out += "    @app.task(name='%s_%s')\n" % (name,
                                                              method_name)

                out += "%s\n" % line

            if line.strip().find("class") == 0:
                state = "class"
        out += "\n"
        return out

    def getCodeServer(self):
        path = self.actorsPath
        if not j.sal.fs.exists(path=path):
            raise j.exceptions.Input("could not find actors path:%s" % path)
        code = ""
        for item in j.sal.fs.listFilesInDir(path, filter="*.py", recursive=False, followSymlinks=True):
            code += self._getCode(item)
        return code

    def getCodeClient(self, actorName):
        path2 = "%s/%s.py" % (self.actorsPath, actorName)
        if not j.sal.fs.exists(path=path2):
            raise j.exceptions.Input("could not find actor path:%s" % path2)
        code = self._getCode(path2)
        return code

    def celery_start(self, concurrency=4, actorsPath="actors"):

        from celery import Celery

        j.clients.redis.core_start()

        app = Celery('tasks', broker=self.url)

        app.conf.update(
            CELERY_TASK_SERIALIZER='json',
            CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
            CELERY_RESULT_SERIALIZER='json',
            CELERY_TIMEZONE='Europe/Oslo',
            CELERY_ENABLE_UTC=True,
            # CELERY_RESULT_BACKEND='rpc',
            CELERY_RESULT_PERSISTENT=True,
            CELERY_RESULT_BACKEND=self.url,
        )

        app.conf["CELERY_ALWAYS_EAGER"] = False
        app.conf["CELERYD_CONCURRENCY"] = concurrency

        code = self.getCodeServer()
        exec(code, locals(), globals())

        app.worker_main()

    def celery_client_get(self, actorName, local=False):

        if actorName in self.actors:
            return self.actors[actorName]

        if self.app is None:

            from celery import Celery

            app = Celery('tasks', broker=self.url)

            app.conf.update(
                CELERY_TASK_SERIALIZER='json',
                CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
                CELERY_RESULT_SERIALIZER='json',
                CELERY_TIMEZONE='Europe/Oslo',
                CELERY_ENABLE_UTC=True,
                # CELERY_RESULT_BACKEND='rpc',
                CELERY_RESULT_PERSISTENT=True,
                CELERY_RESULT_BACKEND=self.url,
            )

            # if local:
            #     app.conf["CELERY_ALWAYS_EAGER"] = False

            self.app = app
        else:
            app = self.appactorName

        code = self.getCodeClient(actorName=actorName)
        exec(code, locals(), globals())

        self.actors[actorName] = eval("%s" % actorName)

        return self.actors[actorName]
