from js9 import j
import os
import cson

import inspect


class AtomEditor:

    def __init__(self):
        self.__jslocation__ = "j.tools.atom"
        self.__imports__ = "cson"
        self._packages = []

    @property
    def packages(self):
        """
        Lists all atom packages installed on your system.
        """
        if self._packages == []:
            cmd = "apm list -b"
            rc, out, err = j.sal.process.execute(cmd, die=True, showout=False)
            items = [item.split("@")[0] for item in out.split("\n") if item.strip() != ""]
            self._packages = items

        return self._packages

    def installPackage(self, name, upgrade=False):
        if name.strip() is "":
            return
        name = name.strip()
        if name.startswith("#"):
            return
        if upgrade is False and name in self.packages:
            return
        cmd = "apm install %s" % name
        j.sal.process.execute(cmd, die=True, showout=False)

    def installAll(self):
        self.installPythonExtensions()
        self.installPackagesAll()
        self.installSnippets()
        self.installConfig()

    def installPackagesAll(self):
        self.installPackagesMarkdown()
        self.installPackagesRaml()
        self.installPackagesPython()
        self.installPackagesNim()

    def installPackagesMarkdown(self):
        "Installs packages for markdown"
        items = """
        language-markdown
        markdown-folder
        markdown-mindmap
        markdown-pdf
        markdown-scroll-sync
        markdown-toc
        tidy-markdown
        markdown-preview
        language-gfm
        """
        for item in items.split("\n"):
            self.installPackage(item)

    def installPackagesNim(self):
        "Installs main nim packages."
        items = """
        nim
        """
        for item in items.split("\n"):
            self.installPackage(item)

    def installPackagesPython(self):
        "Installs main python packages."
        items = """
        language-capnproto
        todo-manager
        git-time-machine
        flatten-json
        bottom-dock
        autocomplete-python
        linter
        linter-flake8
        linter-python-pep8
        # linter-python-pyflakes
        # linter-pep8
        python-autopep8
        """
        for item in items.split("\n"):
            self.installPackage(item)

    def installPackagesRaml(self):
        "Installs RAML api-workbench package."
        items = """
        api-workbench
        """
        for item in items.split("\n"):
            self.installPackage(item)

    def installSnippets(self):
        """Adds Jumpscale snippets to your atom snippets file."""

        # Note : to add more snippets you they need to be on the same 'key'
        # so we will do a snippets merge based on keys.
        print("install snippets")
        merged = {}
        snippets_existing_path = os.path.expanduser("~/.atom/snippets.cson")

        snippetspath = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "snippets.cson")
        if j.sal.fs.exists(snippets_existing_path, followlinks=True):
            snippets_existing = j.sal.fs.fileGetContents(snippets_existing_path)
            snippets_existing2 = ""
            for line in snippets_existing.split("\n"):
                if line.startswith("#") or line.strip == "":
                    continue
                snippets_existing2 += line

            if snippets_existing2.strip == "":
                merged = cson.loads(snippets_existing2)
                with open(snippetspath) as jssnippets:
                    snippets = cson.load(jssnippets)
                    for k, v in snippets.items():
                        if k in merged:
                            merged[k].update(snippets[k])
                content = cson.dumps(merged, indent=4, sort_keys=True)
            else:
                content = j.sal.fs.fileGetContents(snippetspath)
            j.sal.fs.writeFile(os.path.expanduser("~/.atom/snippets.cson"), content)
        else:
            nc = j.sal.fs.fileGetContents(snippetspath)
            j.sal.fs.writeFile(filename=snippets_existing_path, contents=nc, append=False)

    def installConfig(self):
        print("install atom config")
        merged = {}
        current_config = j.sal.fs.fileGetContents(os.path.expanduser("~/.atom/config.cson"))
        merged = cson.loads(current_config)
        new_config_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "config.cson")
        new_config_content = j.sal.fs.fileGetContents(new_config_path)
        new_config = cson.loads(new_config_content)

        for k, v in new_config.items():
            if k in merged:
                merged[k].update(new_config[k])
            else:
                merged[k] = v
        content = cson.dumps(merged, indent=4, sort_keys=True)
        j.sal.fs.writeFile(os.path.expanduser("~/.atom/config.cson"), content)

    def generateJumpscaleAutocompletion(self, dest="/usr/local/lib/python3.5/dist-packages/jscompl.py"):
        # 1- generate the docs & the pickled js8 api.
        j.tools.objectinspector.generateDocs(dest="/tmp")
        # 2- generate the stub (jscompl.py) from the pickled file.
        j.tools.js8stub.generateStub(pickledfile='/tmp/out.pickled')

        # 3- move the stub to dist-packages
        j.sal.fs.moveFile("/tmp/jscompl.py", dest)

    def installPythonExtensions(self):
        """
        pip installs flake8, autopep8.
        """

        C = """
        pip3 install autopep8
        pip3 install flake8
        pip3 install flake8-docstrings
        """
        rc, out, err = j.sal.process.execute(C, die=True, showout=False, ignoreErrorOutput=False)
