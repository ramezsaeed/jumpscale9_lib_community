
from js9 import j


def xonsh_go(args, stdin=None):
    lookfor = args[0]
    # walk over github dirs, try to find lookfor
    res = []
    for subdir in j.sal.fs.listDirsInDir(j.dirs.CODEDIR + "/github/", False, True):
        curpath = "%s/github/%s/" % (j.dirs.CODEDIR, subdir)
        for subdir2 in j.sal.fs.listDirsInDir(curpath, False, True):
            curpath2 = j.sal.fs.joinPaths(curpath, subdir2)
            print(curpath2)
            if subdir2.find(lookfor) != -1:
                res.append(curpath2)
    path = j.tools.console.askChoice(res, "Select directory to go to.")

    if len(args) > 1:
        # means look for subdir in found current path
        res = j.sal.fs.listDirsInDir(path, True)
        res = [item for item in res if j.sal.fs.getBaseName(item)[0] != "."]
        res = [item for item in res if j.sal.fs.getBaseName(item).find(args[1]) != -1]
        path = j.tools.console.askChoice(res, "Select sub directory to go to.")

    j.sal.fs.changeDir(path)


def xonsh_edit(args, stdin=None):
    if len(args) == 0:
        cmd = "/Applications/Sublime\ Text.app/Contents/SharedSupport/bin/subl -a ."
        j.sal.process.executeInteractive(cmd)
        return
    else:
        items = [item for item in j.sal.fs.listFilesInDir(
            j.sal.fs.getcwd(), exclude=["*.pyc"]) if j.sal.fs.getBaseName(item).find(args[0]) != -1]
        if len(items) == 0:
            print("cannot find file with filter '%s' in %s" % (args[0], j.sal.fs.getcwd()))
            sys.exit()
        path = j.tools.console.askChoice(items, "Select file to edit.")

    if j.sal.fs.exists("/Applications/Sublime Text.app"):
        # osx
        cmd = "open -a Sublime\ Text %s" % path

    elif j.sal.fs.exists("/usr/bin/subl"):
        raise j.exceptions.RuntimeError("please implement xonsh_edit for linux")  # TODO: *2
    else:
        raise j.exceptions.RuntimeError("Did not find editor")

    j.sal.process.executeInteractive(cmd)


def xonsh_update(args, stdin=None):
    print("update git repo's")
    j.tools.xonsh.configAll()
    # j.sal.process.execute("jscode update -a jumpscale -n play8")
    # j.sal.process.execute("jscode update -a jumpscale -n play8")
    # j.sal.process.execute("jscode update -a jumpscale -n play8")


# def xonsh_git(args, stdin=None):
#     def checkdir():
#         from IPython import embed
#         print ("DEBUG NOW checkdir")
#         embed()

#     if len(args)==0:
#         H="""
#         for these commands to work you need to be in git directory

#         jsgit commit 'message'  # will commit, pull & merge
#         jsgit push 'message'    # will commit, pull & merge & push
#         jsgit branch mybranch   # will create/get branch, then commit
#         jsgit pull remoteUrl    # no need to specify location where to pull, will go there directly
#         jsgit reset             # will remove local changes & go to trunk
#         """
#         return
#     elif len(args)==1:
#         cmd=args[0]
#         if cmd=="reset":
#             cmd = 'cd %s; git checkout .' % path
#             j.sal.process.execute(cmd)
#             j.clients.git.pullGitRepo(url=client.remoteUrl)
#     elif len(args)==2:
#         cmd=args[0]
#         data=args[1]
#         if cmd=="pull":
#             j.clients.git.pullGitRepo(data, dest=None, depth=None,
#                          ignorelocalchanges=opts.deletechanges, reset=False, branch=opts.branch)
#         elif cmd=="push":


#     else:
#         raise j.exceptions.RuntimeError("need to specify 1 or 2 args.\n%s"%H)

#     j.sal.process.executeInteractive(cmd)
