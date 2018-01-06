from js9 import j


class Mountable:
    """
    Abstract implementation for devices that are mountable.
    Device should have attributes devicename and mountpoint
    """

    def mount(self, target, options=['defaults']):
        """
        @param target: Mount point
        @param options: Optional mount options
        """
        if self.mountpoint == target:
            return

        self._client.bash('mkdir -p {}'.format(target))

        self._client.disk.mount(
            source=self.devicename,
            target=target,
            options=options,
        )

        self.mountpoint = target

    def umount(self):
        """
        Unmount disk
        """
        if self.mountpoint:
            self._client.disk.umount(
                source=self.mountpoint,
            )
        self.mountpoint = None


class AYSable:
    """
    Abstract implementation for class that reflect an AYS service.
    class should have a name and actor attributes

    This provide common method to CRUD AYS service from the python classes
    """
    @property
    def name(self):
        return self._obj.name

    @property
    def role(self):
        return self.actor.split('.')[0]

    def create(self, aysrepo):
        """
        create the AYS Service
        """
        raise NotImplementedError()

    def get(self, aysrepo):
        """
        get the AYS service
        """
        try:
            return aysrepo.serviceGet(role=self.role, instance=self.name)
        except j.exceptions.NotFound:
            raise ValueError("Could not find {} with name {}".format(self.role, self.name))
