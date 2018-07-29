from js9 import j
import sys

JSBASE = j.application.jsbase_get_class()

class DocFixer(JSBASE):
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.tools.docfixer"
        JSBASE.__init__(self)

    def load(self,path=""):
        """
        js9 'j.tools.docfixer.load()'
        """
        j.clients.redis.core_check()

        if not path:
            path = j.sal.fs.getcwd()

        if not j.sal.fs.exists(path=path):
            raise j.exceptions.NotFound("Cannot find source path in load:'%s'" % path)

        j.sal.fs.remove(path + "errors.md")

        def clean(name):
            return j.data.text.strip_to_ascii_dense(name)

        def callbackForMatchDir(path, arg):
            base = j.sal.fs.getBaseName(path).lower()

            if base.startswith("_"):
                return False

            return True

        def callbackForMatchFile(path, arg):
            
            base = j.sal.fs.getBaseName(path).lower()

            if base == "_sidebar.md":
                return True

            if base.startswith("_"):
                return False

            ext = j.sal.fs.getFileExtension(path)

            if not ext in ["md", "yaml", "toml"]:
                return False

            if ext == "md" and base[:-3] in ["summary", "default"]:
                return False

            return True

        def callbackFunctionDir(path, arg):
            # will see if ther eis data.toml or data.yaml & load in data structure in this obj
            self._processData(path + "/data")
            dpath = path + "/default.md"
            if j.sal.fs.exists(dpath, followlinks=True):
                C = j.sal.fs.fileGetContents(dpath)
                rdirpath = j.sal.fs.pathRemoveDirPart(path, self.path)
                rdirpath = rdirpath.strip("/").strip().strip("/")
                self.content_default[rdirpath] = C
            return True

        def callbackFunctionFile(path, arg):
            self.logger.debug("file:%s"%path)
            ext = j.sal.fs.getFileExtension(path).lower()
            base = j.sal.fs.getBaseName(path)
            if ext == "md":
                self.logger.debug("found md:%s"%path)
                base = base[:-3]  # remove extension
                doc = Doc(path, base, docsite=self)
                # if base not in self.docs:
                #     self.docs[base.lower()] = doc
                self.docs[doc.name_dot_lower] = doc
            elif ext in ["html","htm"]:
                self.logger.debug("found html:%s"%path)
                l = len(ext)+1
                base = base[:-l]  # remove extension
                doc = HtmlPage(path, base, docsite=self)
                # if base not in self.htmlpages:
                #     self.htmlpages[base.lower()] = doc
                self.htmlpages[doc.name_dot_lower] = doc
            else:
                
                if ext in ["png", "jpg", "jpeg", "pdf", "docx", "doc", "xlsx", "xls", \
                            "ppt", "pptx", "mp4","css","js"]:
                    self.logger.debug("found file:%s"%path)
                    if base in self.files:
                        raise j.exceptions.Input(message="duplication file in %s,%s" %
                                                 (self, path), level=1, source="", tags="", msgpub="")
                    self.files[base.lower()] = path
                # else:
                #     self.logger.debug("found other:%s"%path)
                #     l = len(ext)+1
                #     base = base[:-l]  # remove extension
                #     doc = DocBase(path, base, docsite=self)
                #     if base not in self.others:
                #         self.others[base.lower()] = doc
                #     self.others[doc.name_dot_lower] = doc
                    

        callbackFunctionDir(self.path, "")  # to make sure we use first data.yaml in root

        j.sal.fswalker.walkFunctional(
            self.path,
            callbackFunctionFile=callbackFunctionFile,
            callbackFunctionDir=callbackFunctionDir,
            arg="",
            callbackForMatchDir=callbackForMatchDir,
            callbackForMatchFile=callbackForMatchFile)

    def error_raise(self, errormsg, doc=None):
        if doc is not None:
            errormsg2 = "## ERROR: %s\n\n- in doc: %s\n\n%s\n" % (j.data.time.getLocalTimeHR(), doc, errormsg)
            j.sal.fs.writeFile(filename=self.path + "errors.md", contents=errormsg2, append=True)
            self.logger.error(errormsg2)
            doc.errors.append(errormsg)
        else:
            from IPython import embed
            self.logger.error("DEBUG NOW raise error")
            embed()
            raise RuntimeError("stop debug here")
