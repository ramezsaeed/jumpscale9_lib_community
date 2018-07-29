
from js9 import j
# issues still not implemented

# use gogs from 0-complexity and go-gogs-client from 0-complexity
# url = https://github.com/0-complexity/gogs
# url = https://github.com/0-complexity/go-gogs-client

import requests
from requests.auth import HTTPBasicAuth
from random import randint
import sys

JSBASE = j.application.jsbase_get_class()


class GogsBaseException(Exception, JSBASE):
    def __init__(self):
        JSBASE.__init__(self)


class AdminRequiredException(GogsBaseException):
    def __init__(self):
        GogsBaseException.__init__(self)


class DataErrorException(GogsBaseException):
    def __init__(self):
        GogsBaseException.__init__(self)


class NotFoundException(GogsBaseException):
    def __init__(self):
        GogsBaseException.__init__(self)


class GogsServerErrorException(GogsBaseException):
    def __init__(self):
        GogsBaseException.__init__(self)


baseurl = "{addr}/api/v1"


states = ["new", "inprogress", "question", "wontfix", "resolved", "closed"]  # prefix: state_
state_color_code = '#c2e0c6'
types_proj = ["alert", "incident", "task", "question", "story", "request"]  # prefix: type_
types_code = ["documentation", "feature", "bug", "question"]  # prefix: priority_
types_color_code = '#fef2c0'
priorities = ["critical", "major", "normal", "minor"]  # prefix: type
prio_color_code = '#f9d0c4'

TEMPLATE = """
addr = ""
port = 3000
password_ = ""
login = ""
token_ = ""
"""


JSConfigBase = j.tools.configmanager.base_class_config


class GogsClient(JSConfigBase):

    # def __init__(self, addr, login="root", passwd="root", port=3000, accesstoken=None):
    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigBase.__init__(self, instance=instance, data=data, parent=parent, template=TEMPLATE, interactive=interactive)
        c = self.config.data
        addr = c["addr"]
        if not addr.startswith("http"):
            addr = "http://{addr}".format(addr=addr)
        self.addr = addr + ":{port}".format(port=c['port'])
        self.login = c['login']
        self.password = c['password_']
        self.port = c['port']
        self.baseurl = baseurl.format(addr=self.addr)
        self.session = requests.session()
        if not c['token_']:
            self.session.auth = HTTPBasicAuth(self.login, self.password)
        else:
            self.session.headers['Authorization'] = 'token {}'.format(c['token_'])

        self.logger.info("gogs client initted:%s for user %s" % (self.addr, self.login))

    def test(self):

        # TODO:
        # BUILD GO
        # GO GET OUR GIGFORK/GOGS and BUILD IT

        # set login credentials.
        addr = "http://localhost"
        port = 3000
        self.addr = addr + ":{port}".format(port=port)
        self.login = "root"
        self.password = "root"
        self.port = port
        self.baseurl = baseurl.format(addr=self.addr)
        self.session = requests.session()
        self.session.auth = HTTPBasicAuth(self.login, self.password)

        testrep = "mytestrep6"
        testorg = "mytestorg6"
        testuser = "testuser6oat"

        def dump_all():
            self.logger.debug(self.reposList())
            self.logger.debug(self.usersList())
            self.logger.debug(self.organizationsList())

        try:
            self.repoGet(testrep, "root")
        except BaseException:
            self.repoCreate(reponame=testrep, username="root", description="simple test repo")
        try:
            self.userGet(testuser)
        except BaseException:
            self.userCreate(testuser, testuser, "test_user@fake.com")

        try:
            self.organizationGet(testorg)
        except BaseException:
            self.organizationCreate(testorg)
        dump_all()

        self.logger.debug(self.userGet("root"))
        # CREATE TEST repo
        self.logger.debug(self.repoGet(testrep))

        self.repoAddCollaborator(testrep, testuser, "root")
        self.repoRemoveCollaborator(testrep, testuser, "root")

        self.organizationAddUser(testorg, testuser)
        self.organizationRemoveUser(testorg, testuser)
        self.issuesList(testrep)
        self.issueCreate(testrep, "really doesnt work", "root", "it doesnt compile")
        self.issueCreate(testrep, "really doesnt work2", "root", "it doesnt build")
        self.logger.debug(self.issuesList(testrep))
        self.logger.debug(self.issueGet(testrep, 1, "root"))
        # dump_all()
        self.issueClose(testrep, 1)
        self.logger.debug(self.issuesList(testrep))

        dump_all()

    def build_url(self, *args):

        res = j.sal.fs.joinPaths(self.baseurl, *args)
        self.logger.debug("git_host_url:%s" % res)
        return res

    def reposList(self, owner=None):
        """
        return list of all repositories owned by the logged in user.
        @return
        [[$id,$name,$ssh_url]]
        """
        if not owner:
            owner = self.login
        self.logger.debug("repos list for owner:%s" % owner)
        respone_user = self.userGet(owner)
        response_repos = self.session.get(self.build_url("repos", "search"), params={
                                          'uid': respone_user['id'], 'limit': sys.maxsize})
        repos = list()
        if response_repos.status_code == 200:
            for repo in response_repos.json()['data']:
                repos.append([repo['id'], repo['full_name'], repo['ssh_url']])
            return repos
        else:
            raise GogsBaseException()

    def repoCreate(self, reponame, organization=None, username=None,
                   description="", private=True, readme=True):
        """
        Create a repository for the owned by the loggedin user.

        @param reponame string: repository name.
        @param organization string: the owning organization.
        @param username string: the owner.
        @param description string: description of the repository.
        """
        body = {
            "name": reponame,
            "description": description,
            "private": private,
            "readme": "default"
        }
        if username and organization:
            raise DataErrorException(
                'username and organization are mutually exclusive')

        if organization:
            response_set = self.session.post(
                self.build_url("admin", "users", organization, "repos"), json=body)
        elif username:
            response_set = self.session.post(
                self.build_url("admin", "users", username, "repos"), json=body)
        else:
            response_set = self.session.post(
                self.build_url("user", "repos"), json=body)

        if response_set.status_code == 200:
            return response_set.json()[0]
        elif response_set.status_code == 422:
            raise DataErrorException(
                "%s is required or already exists" % response_set.json()['message'])
        elif response_set.status_code == 403:
            raise AdminRequiredException('Admin access Required')

    def repoGet(self, reponame, owner=None):
        """
        Get repo (reponame) owned by owner (or the current logged in user.)
        """
        if not owner:
            owner = self.login

        response_user = self.session.get(
            self.build_url("repos", owner, reponame))
        if response_user.status_code == 200:
            return response_user.json()
        elif response_user.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    #  WASN'T IMPLEMENTED IN THE ORIGINAL CLIENT.
    def repoUpdate(self, args):
        raise NotImplementedError

    def repoDelete(self, reponame, owner=None):
        """
        Delete repository reponame

        @param reponame string: name of the repository.
        """
        if not owner:
            owner = self.login

        response_delete = self.session.delete(
            self.build_url("repos", owner, reponame))
        if response_delete.status_code == 204:
            return True
        elif response_delete.status_code == 403:
            raise AdminRequiredException(
                'loged in user is a owner of the repository')
        else:
            raise NotFoundException()

    def repoAddCollaborator(self, reponame, username, owner=None, access="RW"):
        """
        Add collaborator (username) to  repository (reponame)

        @param reponame string: name of the repository.
        @param username string: username of the collaborator.
        @param owner string: owner of the repository to add a collaborator to.
        @param access string: defaults to RW (read write access).
        """

        if not owner:
            owner = self.login

        body = {
            "permission": access
        }

        # testing to see if user has access
        self.repoGet(reponame, owner)

        response_repos = self.session.put(
            self.build_url("repos", owner, reponame, "collaborators", username), json=body)
        if response_repos.status_code in [200, 204]:
            return True
        else:
            raise DataErrorException()

    def repoRemoveCollaborator(self, reponame, username, owner=None):
        """
        Remove user `username` from collaborators of reposiotry reponame

        @param reponame string: repository name.
        @param username string: collaborator name.
        @param owner string: owner of the repository
        """
        access = "NOACCESS"
        if not owner:
            owner = self.login

        body = {
            "permission": access
        }

        # testing to see if user has access
        self.repoGet(reponame, owner)

        response_repos = self.session.delete(
            self.build_url("repos", owner, reponame, "collaborators", username), json=body)

        if response_repos.status_code in [200, 204]:
            return True
        else:
            raise DataErrorException()

    def usersList(self):
        """
        Get list of all users available in Gogs.
        """
        req_url = self.baseurl + "/users"
        response_list = self.session.get(req_url)

        if response_list.status_code == 200:
            return response_list.json()
        elif response_list.status_code == 500:
            raise GogsServerErrorException()

    def userGet(self, username):
        """
        Get `user` username.
        """
        URL = self.baseurl + "/users/{username}"
        req_url = URL.format(username=username)
        if not username:
            username = self.login

        response_user = self.session.get(req_url)
        if response_user.status_code == 200:
            return response_user.json()
        else:
            raise NotFoundException()

    def userCreate(self, login_name, username, email):
        """
        Create new user.

        @param login_name string: login name
        @param username string: username
        @param email string: user email.
        """
        body = {
            "login_name": login_name,
            "username": username,
            "email": email
        }
        resp = self.session.post(
            self.build_url("admin", "users"), json=body)

        if resp.status_code in [201, 200]:
            return True
        return False

    def userUpdate(self, name, email, pubkey=None, **args):
        """
        Creates user, if user exists then will just set the email & pubkey.

        @param name string: username.
        @param email string: email.
        @param pubkey string: public key.
        """
        body = {
            "login_name": name,
            "username": name,
            "email": email
        }

        def pubkey_name():
            pubkey_name = 'pubkey%d' % (randint(1, 100))
            response_exists = self.session.get(
                '%s/user/keys/%s' % (self.baseurl, pubkey_name))
            if response_exists.status_code == 404:
                return pubkey_name
            else:
                pubkey_name()

        if pubkey:
            data = {"title": pubkey_name(), "key": pubkey}
            response_pubk = self.session.post(
                self.build_url("user", "keys"), json=data)
            if response_pubk.status_code == 422:
                raise DataErrorException('pubkey exists or is invalid')

        try:
            self.userGet(name)
            response_set = self.session.patch(
                '%s/admin/users/%s' % (self.baseurl, name), json=body)
        except NotFoundException:
            response_set = self.session.post(
                self.build_url("admin", "users"), json=body)

        if response_set.status_code == 201:
            return True
        elif response_set.status_code == 422:
            raise DataErrorException(
                "%s is required or already exists" % response_set.json()[0]['message'])
        elif response_set.status_code == 403:
            raise AdminRequiredException('Admin access Required')

    def userDelete(self, username):
        """
        Delete a user with provided username.

        @param username string: username to delete.
        """
        req_url = self.baseurl + "/admin/users/" + username

        response_delete = self.session.delete(req_url)

        if response_delete.status_code in [204, 200]:
            return True
        elif response_delete.status_code == 403:
            raise AdminRequiredException('Admin access required')
        elif response_delete.status_code == 422:
            raise DataErrorException("data is required but not provided")
        elif response_delete.status_code == 404:
            raise NotFoundException()
        elif response_delete.status_code == 500:
            raise GogsServerErrorException('gogs server error')

    def organizationsList(self, username=None):
        """
        List organizations of current user
        """
        if not username:
            response_orgs = self.session.get(self.build_url("orgs"))
        else:
            response_orgs = self.session.get(
                self.build_url("users", username, "orgs"))
        if response_orgs.status_code == 200:
            return response_orgs.json()

    def organizationGet(self, orgname=None):
        """
        Get organization `orgname` record.

        @param orgname string: organization name.
        """
        url = self.build_url("orgs", orgname)
        self.logger.debug("organizationGet::", url)
        response_org = self.session.get(url)
        if response_org.status_code == 200:
            return response_org.json()
        elif response_org.status_code == 403:
            raise AdminRequiredException('Admin access required')
        elif response_org.status_code == 422:
            raise DataErrorException("data is required but not provided")
        elif response_org.status_code == 404:
            raise NotFoundException()
        elif response_org.status_code == 500:
            raise GogsServerErrorException('gogs server error')

    def organizationCreate(self, orgname, full_name=None, username=None,
                           description=None, website=None, location=None):
        """
        Create new organization.

        @param orgname string: organization name.
        @param full_name string: full name of the organization.
        @param username: string: username
        @param description string: organization description.
        @param location string: location.
        """
        if not username:
            username = self.login
        if not full_name:
            full_name = orgname

        body = {
            "username": orgname,
            "full_name": full_name,
            "description": description,
            "website": website,
            "location": location
        }
        url = self.build_url("orgs")
        response_set = self.session.post(url, json=body)
        # /users/abdu/orgs
        if response_set.status_code in [201, 200]:
            return response_set.json()
        elif response_set.status_code == 422:
            raise DataErrorException(
                "%s is missing or already exists" % response_set.json()[0]['message'])
        elif response_set.status_code == 403:
            raise AdminRequiredException('Admin access Required')

    # NOT IMPLEMENTED.
    def organizationUpdate(self):
        raise NotImplementedError

    def organizationDelete(self, orgname):
        """
        Delete specific organization

        @param orgname string: organization name.
        """
        # Oranization is a user of type organization.
        return self.userDelete(orgname)

    def organizationAddUser(self, orgname, username=None):
        """
        Add user `username` to organization `orgname`.

        @param orgname string: organization name.
        @param username string: username to be added to the organization..

        """

        if username is None:
            username = self.login

        url = self.baseurl + "/users/{username}/org".format(username=username)
        body = {
            "username": orgname
        }
        resp = self.session.post(url, json=body)
        if resp.status_code in [200, 204]:
            return True
        return False

    def organizationRemoveUser(self, orgname, username=None):
        """
        Remove user `username` from organization `orgname`

        @param orgname string: organization name.
        @param username string: username to be removed from organization.
        """
        if username is None:
            username = self.login

        url = self.baseurl + "/users/{username}/org".format(username=username)
        body = {
            "username": orgname
        }
        resp = self.session.delete(url, json=body)
        if resp.status_code in [200, 204]:
            return True
        return False

    def setAllRepoLabels(self, labels=None):
        """
        Set labels to all repos in Gogs.

        @param labels  [(label_name, label_color)]: list of tuples with index 0 label name and index 1 label color.
        """
        owners = self.usersList()
        owners += self.organizationsList()

        for owner in owners:
            self.ownerSetLabels(owner['username'], labels)

    def issuesList(self, reponame, owner=None):
        """
        List all issues owned by owner in repositroy reponame

        @param reponame string: repository name.
        """

        if not owner:
            owner = self.login

        response_list = self.session.get(
            self.build_url("repos", owner, reponame, "issues"))

        if response_list.status_code == 200:
            return response_list.json()
        elif response_list.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def issueGet(self, reponame, index, owner=None):
        """
        Get issue from repo owned by owner at index

        @param reponame string: repository name.
        @param index int:  issue id.
        @param owner string: repository owner
        """
        if isinstance(index, int):
            index = str(index)

        if not owner:
            owner = self.login

        response_get = self.session.get(
            "%s/repos/%s/%s/issues/%s" % (self.baseurl, owner, reponame, index))

        if response_get.status_code == 200:
            return response_get.json()
        elif response_get.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def issueCreate(
            self,
            reponame,
            title,
            owner=None,
            description=None,
            assignee=None,
            milestone=None,
            labels=None,
            closed=None):
        """
        create issue
        @milestone  = int
        @id = int
        owner can be user or organization
        """

        body = {
            "title": title,
            "body": description,
            "assignee": assignee,
            "milestone": milestone,
            "labels": labels,
            "closed": closed
        }
        if owner is None:
            owner = self.login

        response_create = self.session.post(
            self.build_url("repos", owner, reponame, "issues"), json=body)

        if response_create.status_code == 201:
            return response_create.json()
        elif response_create.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def issueAddLabels(self, repo, issue_index, labels, owner=None):
        if not owner:
            owner = self.login

        body = {
            "labels": labels
        }

        response_list = self.session.post(
            self.build_url("repos", owner, repo, "issues", issue_index, "labels"), body)

        if response_list.status_code == 200:
            return response_list.json()
        elif response_list.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def issueUpdate(self):
        raise NotImplementedError

    #  ISSUE DELETE
    def issueDelete(self):
        raise NotImplementedError

    def issueClose(self, reponame, index, owner=None):
        """
        Close issue

        @param reponame string: repository name.
        @param index int: issue id.
        @param owner string: repository owner (or the current logged in user).
        """

        if isinstance(index, int):
            index = str(index)

        if not owner:
            owner = self.login

        body = {"state": "closed"}

        response_close = self.session.patch(
            self.build_url("repos", owner, reponame, "issues", index), json=body)

        if response_close.status_code == 201:
            return response_close.json()
        elif response_close.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def labelCreate(self, reponame, label_name, label_color, owner=None):
        if not owner:
            owner = self.login
        if label_name in self.labelList(reponame, owner):
            return {}
        body = {
            "name": label_name,
            "color": label_color
        }

        response_create = self.session.post(
            self.build_url("repos", owner, reponame, "labels"), json=body)

        if response_create.status_code == 201:
            return response_create.json()
        elif response_create.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    def labelUpdate():
        pass

    def labelDelete(self, reponame, label_name, owner=None):
        if not owner:
            owner = self.login

        try:
            label = self.labelGetByName(reponame, label_name, owner)
        except NotFoundException:
            return True

        url = self.build_url("repos", owner, reponame, "labels", str(label['id']))
        response = self.session.delete(url)
        return response.status_code == 204

    def labelGetByName(self, reponame, label_name, owner=None):
        if not owner:
            owner = self.login
        for label in self.labelList(reponame, owner, details=True):
            if label['name'] == label_name:
                return label

        raise NotFoundException("Label {} not found at {}/{}".format(label_name, owner, reponame))

    def labelList(self, reponame, owner=None, details=False):
        if not owner:
            owner = self.login

        response_list = self.session.get(
            self.build_url("repos", owner, reponame, "labels"))

        if response_list.status_code == 200:
            labellist = list()
            labels = response_list.json()
            if details is False:
                for label in labels:
                    labellist.append(label['name'])
                return labellist
            else:
                return labels
        elif response_list.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")

    # def labelsSet(self, reponame=None, owner=None):
    #     """If owner or reponame is None then will walk over all."""

    def ownerDeleteLabels(self, owner):
        """delete all labels from the owner"""
        self.logger.debug("delete unneeded labels for:%s" % owner)
        repos = self.reposList(owner=owner)
        alllabels = ['state_{}'.format(state) for state in states]
        alllabels += ['type_{}'.format(type_) for type_ in types_proj]
        alllabels += ['type_{}'.format(type_) for type_ in types_code]
        alllabels += ['priority_{}'.format(prio) for prio in priorities]
        for repo in repos:
            repoid, fullreponame, reposshurl = repo
            reponame = fullreponame.split('/')[-1]
            for label in self.labelList(reponame, owner=owner):
                if label not in alllabels:
                    self.logger.debug("remove label:%s:%s" % (owner, label))
                    self.labelDelete(reponame, label, owner=owner)

    def ownerSetLabels(self, owner, reset=False):
        """
        Set labels for all repos in organization or user.

        @param owner string: organization name.
        """
        if reset:
            self.ownerDeleteLabels(owner)
        repos = self.reposList(owner=owner)
        result = list()
        for repo in repos:
            repoid, fullreponame, reposshurl = repo
            reponame = fullreponame.split('/')[-1]
            if reponame.startswith("proj_") or reponame.startswith(
                    "env_") or reponame.startswith("org_")or reponame.startswith("cockpit_"):
                types = types_proj
            else:
                types = types_code
            for state in states:
                labelname, labelcolor = "state_{}".format(state), state_color_code
                result.append(self.labelCreate(reponame, labelname, labelcolor, owner))
            for type_ in types:
                labelname, labelcolor = "type_{}".format(type_), types_color_code
                result.append(self.labelCreate(reponame, labelname, labelcolor, owner))
            for prio in priorities:
                labelname, labelcolor = "priority_{}".format(prio), prio_color_code
                result.append(self.labelCreate(reponame, labelname, labelcolor, owner))
        return result

    def milestonesList(self, reponame, owner):
        response_milestones = self.session.get(
            self.build_url("repos", owner, reponame, 'milestones'))
        if response_milestones.status_code == 200:
            return response_milestones.json()

    def milestoneCreate(self, reponame, milestone, owner=None):
        if not owner:
            owner = self.login
        milestones = [milestone['title'] for milestone in self.milestonesList(reponame, owner)]
        if milestone in milestones:
            return {}
        if not milestone:
            return {}
        body = {
            "title": milestone,
        }

        response_create = self.session.post(
            self.build_url("repos", owner, reponame, "milestones"), json=body)

        if response_create.status_code == 201:
            return response_create.json()
        elif response_create.status_code == 403:
            raise AdminRequiredException("user does not have access to repo")
        else:
            raise NotFoundException("User or repo does not exist")


    def milestoneDelete(self, reponame, milestone, owner=None):
        if not owner:
            owner = self.login

        milestones = [m for m in self.milestonesList(reponame, owner) if m['title'] == milestone]
        if not milestones:
            return {}

        for milestone in milestones:
            url = self.build_url("repos", owner, reponame, "milestones", str(milestone['id']))
            response = self.session.delete(url)
        return response.status_code == 204
