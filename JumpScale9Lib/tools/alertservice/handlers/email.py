from js9 import j
from JumpScale9Lib.tools.alertservice.AlertService import Handler


class EmailAlerter(Handler):
    ORDER = 50

    def __init__(self, service):
        self.service = service

    def escalate(self, alert, users):
        allemails = set()
        for user in users:
            useremails = self.service.getUserEmails(user)
            for email in useremails:
                allemails.add(email)
        if allemails:
            j.clients.email.send(allemails, 'support@mothership1.com', 'Alert On Mothership1', self.makeMessage(alert))
        return users

    def makeMessage(self, alert):
        alert['url'] = self.service.getUrl(alert)
        message = """Level: %(level)s
Details: %(url)s
Message: %(errormessage)s
""" % alert
        return message
