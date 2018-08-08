
class Monitor:

    def __init__(self, controller, redis_address):
        self.controller = controller
        self.redis_address = redis_address

    def _schedule(self, gid, nid, domain, name, args={}, cron='@every 1m'):
        """
        Schedule the given jumpscript (domain/name) to run on the specified node according to cron specs

        :param gid: Grid id
        :param nid: Node id
        :param domain: jumpscript domain
        :param name: jumpscript name
        :param args: jumpscript arguments
        :param cron: cron specs according to https://godoc.org/github.com/robfig/cron#hdr-CRON_Expression_Format
        :return:
        """
        args = args.update({'redis': self.redis_address})
        #
        # key = '.'.join([str(gid), str(nid), domain, name])
        # self.controller.schedule()

    def _unschedule(self, gid, nid, domain, name):
        """
        Unschedule the given jumpscript

        :param gid: Grid id
        :param nid: Node id
        :param domain: jumpscript domain
        :param name: jumpscript name
        :return:
        """

    def disk(self, gid, nid, args={}, cron='@every 1m'):
        """
        Schedule the disk monitor on the specified node.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass

    def virtual_machine(self, gid, nid, args={}, cron='@every 1m'):
        """
        Schedule the vm monitor on the specified node.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass

    def docker(self, gid, nid, args={}, cron='@every 1m'):
        """
        Schedule the docker monitor on the specified node.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass

    def nic(self, gid, nid, args={}, cron='@every 1m'):
        """
        Schedule the nic monitor on the specified node.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass

    def reality(self, gid, nid, args={}, cron='@every 10m'):
        """
        Schedule the reality reader on the specified node. Reality jumpscript
        will also use the aggregator client to report reality objects.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass

    def logs(self, gid, nid, args={}, cron='@every 1m'):
        """
        Schedule the logs reader on the specified node. Logs jumpscript
        will collects logs from various sources and use the aggregator client
        to report logs.

        :param gid: Grid id
        :param nid: Node id
        :param args: jumpscript arguments
        :param cron: cron specs
        :return:
        """
        pass
