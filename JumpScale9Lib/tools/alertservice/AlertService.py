from js9 import j

import time
import sys
import os
import inspect
import gevent


class Handler:
    ORDER = 50

    def __init__(self, service):
        self.service = service

    def start(self):
        pass

    def updateState(self, alert):
        pass

    def escalate(self, alert, users):
        pass


class AlertService:

    def __init__(self):
        self.__jslocation__ = "j.tools.alertservice"
        self.__imports__ = "gevent"
        self.logger = j.logger.get('j.tools.alertservice')
        # self.rediscl = j.clients.redis.getByInstance('system')
        self.rediscl = j.core.db
        self.alertqueue = self.rediscl.getQueue('alerts')
        self.alerts_client = j.clients.portal.getByInstance('main').actors.system.alerts
        self.handlers = list()
        self.timers = dict()
        self.loadHandlers()
        # TODO *3 ---> get mongoengine connection from AYS
        j.data.models_system.connect2mongo()

    def getUsersForLevel(self, level):
        groupname = "level%s" % level
        users = j.data.models_system.User.find({'groups': {'$all': [groupname, 'alert']}, 'active': True})
        return users

    def getUserEmails(self, user):
        useremails = user['emails']
        if not isinstance(useremails, list):
            useremails = [useremails]
        return useremails

    def loadHandlers(self):
        from JumpScale9Lib.tools.alertservice import handlers
        for name, module in inspect.getmembers(handlers, inspect.ismodule):
            for name, klass in inspect.getmembers(module, inspect.isclass):
                if issubclass(klass, Handler) and klass is not Handler:
                    self.handlers.append(klass(self))
        self.handlers.sort(key=lambda s: s.ORDER)

    def getUrl(self, alert):
        return "http://cpu01.bracknell1.vscalers.com:82/grid/alert?id=%(guid)s" % alert

    def escalate(self, alert):
        level = alert['level']
        users = self.getUsersForLevel(level)
        for handler in self.handlers:
            result = handler.escalate(alert, users)
            if result is not None:
                users = result

    def updateState(self, alert):
        for handler in self.handlers:
            handler.updateState(alert)

    def getAlert(self, id):
        return j.data.models_system.Alert.get(id)

    def escalateHigher(self, alert):
        self.timers.pop(alert['guid'], None)
        message = "Took too long to be Accepted"
        self.logger.info(message + " %s" % alert['guid'])
        self.alerts_client.escalate(alert=alert['guid'], comment=message)

    def start(self, options):
        if options.clean:
            lalerts = self.rediscl.hlen('alerts')
            self.logger.info("Removing cached alerts: %s" % lalerts)
            self.rediscl.delete('alerts')
            self.logger.info("Removing alerts queue: %s" % self.alertqueue.qsize())
            self.rediscl.delete(self.alertqueue.key)

        for handler in self.handlers:
            handler.start()
        self.restartTimers()
        greenlet = gevent.spawn(self.receiveAlerts)
        gevent.joinall([greenlet])

    def getStateTime(self, alert):
        key = "alerter.level%s.%s" % (alert['level'], alert['state'].lower())
        if j.core.state.configGet(key, ""):
            return j.data.time.getDeltaTime(j.core.state.configGet(key))

    def makeTimer(self, alert):
        greenlet = self.timers.get(alert['guid'])
        if greenlet is not None:
            scheduledalert = greenlet.args[0]
            if scheduledalert['state'] != alert['state']:
                self.logger.info("Removing schedule for alert %s" % scheduledalert['state'])
                greenlet.kill()
            else:
                return

        delay = self.getStateTime(alert)
        if delay:
            self.logger.info("Schedule escalation in %ss for state %s" % (delay, alert['state']))
            self.timers[alert['guid']] = gevent.spawn_later(delay, self.escalateHigher, alert)

    def restartTimers(self):
        now = time.time()
        for key, alert in self.rediscl.hgetall('alerts').items():
            alert = self.getAlert(key)
            if alert['state'] in ('RESOLVED', 'UNRESOLVED'):
                self.rediscl.hdel('alerts', key)
            else:
                alerttime = self.getStateTime(alert)
                if not alerttime:
                    self.rediscl.hdel('alerts', key)
                    continue
                epoch = alert['epoch'] or alert['lasttime']
                remainingtime = (epoch + alerttime) - now
                if remainingtime > 0:
                    self.logger.info("Schedule escalation in %ss for state %s" % (remainingtime, alert['state']))
                    self.timers[alert['guid']] = gevent.spawn_later(remainingtime, self.escalateHigher, alert)
                else:
                    self.escalateHigher(alert)

    def receiveAlerts(self):
        while True:
            alertid = self.alertqueue.get()
            alert = self.getAlert(alertid)
            oldalert = self.rediscl.hget('alerts', alertid)
            self.rediscl.hset('alerts', alert['guid'], json.dumps(alert))
            self.logger.info('Got alertid %s' % alertid)
            if alert['state'] == 'ALERT':
                self.escalate(alert=alert)
            elif oldalert:
                oldalert = j.data.serializer.json.loads(oldalert)
                if oldalert['state'] == 'ALERT' and alert['state'] == 'ACCEPTED':
                    alert['message_id'] = oldalert['message_id']
                    self.updateState(alert)
            if alert['state'] in ('RESOLVED', 'UNRESOLVED'):
                self.rediscl.hdel('alerts', alert['guid'])

            self.makeTimer(alert)
