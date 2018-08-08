from jumpscale import j


class Machine:
    """Machine."""

    def poweron(self):
        """Power on the machine."""
        raise NotImplementedError()

    def poweroff(self):
        """Power off the machine."""
        raise NotImplementedError()

    def reboot(self):
        """Reboot the machine."""
        raise NotImplementedError()
