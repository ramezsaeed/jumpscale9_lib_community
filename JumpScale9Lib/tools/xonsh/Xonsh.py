from js9 import j

import xonsh


class Xonsh:

    def __init__(self):
        self.__jslocation__ = "j.tools.xonsh"
        self.__imports__ = "colored-traceback,xonsh,pudb,tmuxp"
        self.executor = j.tools.executorLocal
        self._prefab = self.executor.prefab

    def configAll(self):
        self.config()
        self.configTmux(True)

    def config(self):
        C = """
        from js9 import j
        $XONSH_SHOW_TRACEBACK = True
        $XONSH_STORE_STDOUT = True
        $XONSH_LOGIN = True

        #from pprint import pprint as print

        import colored_traceback
        colored_traceback.add_hook(always=True)
        import sys


        from tools.xonsh.XonshAliases import *

        aliases['jsgo'] = xonsh_go
        aliases['jsedit'] = xonsh_edit
        aliases['jsupdate'] = xonsh_update


        """
        self._prefab.core.file_write("$HOMEDIR/.xonshrc", C)

    def configTmux(self, restart=True):
        self._prefab.system.tmux.configure(restart, True)
