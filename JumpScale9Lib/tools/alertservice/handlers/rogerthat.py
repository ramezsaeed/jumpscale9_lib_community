from js9 import j
from JumpScale9Lib.clients.rogerthat.rogerthatservice import GeventWSServer
from JumpScale9Lib.tools.alertservice.AlertService import Handler
import gevent


class RogerThatAlerter(Handler):
    ORDER = 10
    ANSWERS = [{'id': 'accepted', 'caption': 'Accept', 'action': '', 'type': 'button'},
               {'id': 'escalate', 'caption': 'Escalate', 'action': '', 'type': 'button'}]

    def __init__(self, service):
        self.service = service
        self.rogerthathandler = RogerThatHandler(self)
        self.rogerthatserver = GeventWSServer('0.0.0.0', 5005, self.rogerthathandler)
        self.registeredusers = set()
        self.loadFriends()

    def loadFriends(self):
        for friend in self.rogerthathandler.client.retreive_users():
            self.registeredusers.add(friend['email'])

    def escalate(self, alert, users):
        emails = list()
        for user in users:
            useremails = self.service.getUserEmails(user)
            if self.registeredusers.intersection(useremails):
                emails.append(user['emails'])
        if not emails:
            return users

        message = self.makeMessage(alert)
        answers = self.ANSWERS[:]
        url = self.service.getUrl(alert)
        answers.append({'id': 'details', 'caption': 'Details', 'action': url, 'type': 'button'})
        flags = self.rogerthathandler.client.FLAG_SHARED_MEMBERS
        alertflags = self.rogerthathandler.client.ALERT_FLAG_VIBRATE | self.rogerthathandler.client.ALERT_FLAG_RING_5
        uiflags = self.rogerthathandler.client.FLAG_WAIT_FOR_NEXT_MESSAGE
        message_id = self.rogerthathandler.send_message(message=message, members=emails, answers=answers, tag=alert[
                                                        'guid'], flags=flags, alert_flags=alertflags, ui_flags=uiflags)
        alert['message_id'] = message_id
        self.service.rediscl.hset('alerts', alert['guid'], json.dumps(alert))
        return users

    def updateState(self, alert):
        self.rogerthathandler.send_message(message="User %(assigned_user)s has accepted " %
                                           alert, flags=17, parent_message_key=alert['message_id'], alert_flags=0)

    def start(self):
        return gevent.spawn(self.rogerthatserver.start)

    def makeMessage(self, alert):
        message = """An event has happend on the Mothership1 cloud please investigate.
Level: %(level)s
Message: %(errormessage)s
""" % alert
        return message


class RogerThatHandler:
    API_KEY = j.core.state,configGet('rogerthat.apikey', "")

    def __init__(self, service):
        self.service = service
        self.alerter = service.service
        self.alerts_client = self.alerter.alerts_client
        self.client = j.clients.rogerthat.get(self.API_KEY)

    def send_message(self, **kwargs):
        result = self.client.send_message(**kwargs)
        if result:
            if result['error']:
                print(('Could not send rogerthat message. Message: %(message)s' % result['error']))
                return
            else:
                message_id = result['result']
                return message_id

    def messaging_update(self, params):
        if self.client.checkFlag(params['status'], self.client.STATUS_ACKED):
            user = params['user_details'][0]
            useremail = user['email']
            user = self.getUserByEmail(useremail)
            alertguid = params['tag']
            if not alertguid or params['answer_id'] not in ('accepted', 'escalete'):
                self.alerter.log("Callback from %s with %s" % (user['id'], params['answer_id']))
            elif self.alerter.scl.alert.exists(alertguid):
                if params['answer_id'] == 'accepted':
                    self.alerts_client.update(state='ACCEPTED', alert=params[
                                              'tag'], comment='Via Rogerthat', username=user['id'])
                elif params['answer_id'] == 'escalate':
                    self.alerts_client.escalate(alert=params['tag'], comment='Via Rogerthat', username=user['id'])
            else:
                self.alerter.log("Callback from %s on not existing alert %s" % (user['id'], params['tag']))

    def getUserByEmail(self, email):
        users = self.alerter.scl.user.search({'emails': email})[1:]
        if users:
            return users[0]
        return None

    def friend_invited(self, params):
        email = params['user_details'][0]['email']
        user = self.getUserByEmail(email)
        if user:
            for group in user['groups']:
                if group.startswith('level'):
                    self.service.registeredusers.add(email)
                    return 'accepted'
        return 'declined'

    def __getattr__(self, key):
        def wrapper(params):
            self.alerter.log("Method %s not implemented" % key)
            return
        return wrapper
