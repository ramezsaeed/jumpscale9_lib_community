from js9 import j
import os


class GOLang:

    def __init__(self):
        self.__jslocation__ = "j.tools.golang"
        self._gopath = ""

    def init(self):
        j.tools.bash.addExport("GOPATH", self.gopath)
        j.tools.bash.addPath(self.binpath)
        if j.sal.fs.exists("/usr/local/go/bin/go"):
            j.tools.bash.addPath("/usr/local/go/bin/go")

    @property
    def gopath(self):
        if self._gopath == "":
            if 'GOPATH' in os.environ.keys():
                self._gopath = os.environ["GOPATH"]
            else:
                attempt = j.sal.fs.joinPaths(os.environ["HOME"], "go")
                if j.sal.fs.exists(attempt):
                    os.environ["GOPATH"] = attempt
                else:
                    raise j.exceptions.RuntimeError("Could not find gopath")
                self._gopath = os.environ["GOPATH"]
                self.init()
        return self._gopath

    @property
    def binpath(self):
        _binpath = j.sal.fs.joinPaths(self.gopath, "bin")
        if not j.sal.fs.exists(_binpath):
            raise j.exceptions.RuntimeError("could not find bindir in gopath")

        return _binpath

    def check(self):
        rc, out, err = j.sal.process.execute("which go", showout=False, die=False)
        if rc > 0:
            raise j.exceptions.RuntimeError("Could not find golang, please install")
        self.gopath

    def build(self, url):
        self.check()
        dest = j.data.text.stripItems(url, ["git@", ".git"])
        dest = dest.replace(":", "/")
        dest = j.clients.git.pullGitRepo(url, dest=j.sal.fs.joinPaths(os.environ['GOPATH'], 'src', dest))

        executor = j.tools.executorLocal
        executor.execute('cd %s && godep restore' % dest)
        executor.execute('cd %s && go install' % dest)
        return dest
