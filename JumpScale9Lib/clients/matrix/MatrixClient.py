from js9 import j

JSBaseConfigClient = j.tools.configmanager.base_class_config

# You can either fill username and password to login with or leave them empty to login with itsyouonline credentials
TEMPLATE = """
base_url = ""
user = ""
password_ = ""
"""


def room_check(func):
    """Decorator to check if the client has set a room or not."""

    def wrapped(self, *args, **kwargs):
        if not self.room:
            raise RuntimeError("You must set a room to use by calling set_room method firstly")
        r = func(self, *args, **kwargs)
        return r

    return wrapped


class MatrixClient(JSBaseConfigClient):
    def __init__(self, instance, data=None, parent=None, interactive=False):
        if not data:
            data = {}
        JSBaseConfigClient.__init__(self, instance=instance, data=data, parent=parent,
                                    template=TEMPLATE, interactive=interactive)
        self._client = None
        self.room = None

    @property
    def client(self):
        if self._client is None:
            try:
                from matrix_client.client import MatrixClient
            except ModuleNotFoundError:
                raise ModuleNotFoundError("No matrix client module found, please run j.clients.matrix.install() first")

            self._client = MatrixClient(base_url=self.config.data['base_url'])
            if self.config.data['user'] and self.config.data['password_']:
                self._client.login_with_password(username=self.config.data['user'], password=self.config.data['password_'])
            else:
                jwt = j.clients.itsyouonline.get().jwt
                response = self._client.api.login(login_type="m.login.jwt", token=jwt)
                self._client.user_id = response["user_id"]
                self._client.token = response["access_token"]
                self._client.hs = response["home_server"]
                self._client.api.token = self._client.token
        return self._client

    def create_user(self, username, password):
        return self.client.register_with_password(username, password)

    def create_room(self, alias=None, is_public=False, invitees=()):
        """ Create a new room on the homeserver.

        Args:
            alias (str): The canonical_alias of the room.
            is_public (bool):  The public/private visibility of the room.
            invitees (str[]): A set of user ids to invite into the room.

        Returns:
            Room

        Raises:
            MatrixRequestError
        """
        return self.client.create_room(alias=alias, is_public=is_public, invitees=invitees)

    def join_room(self, room_id_or_alias):
        """ Join a room.

        Args:
            room_id_or_alias (str): Room ID or an alias.

        Returns:
            Room

        Raises:
            MatrixRequestError
        """
        return self.client.join_room(room_id_or_alias)

    def get_rooms(self):
        """ Return a dict of {room_id: Room objects} that the user has joined.

        Returns:
            Room{}: Rooms the user has joined.

        """
        return self.client.get_rooms()

    def get_user(self, user_id):
        """ Return a User by their id.

        NOTE: This function only returns a user object, it does not verify
            the user with the Home Server.

        Args:
            user_id (str): The matrix user id of a user.
        """

        return self.client.get_user(user_id=user_id)

    def upload(self, content, content_type):
        """ Upload content to the home server and receive a MXC url.

        Args:
            content (bytes): The data of the content.
            content_type (str): The mime-type of the content.
        """
        return self.client.upload(content, content_type)

    def set_room(self, room_id):
        try:
            from matrix_client.room import Room
        except ModuleNotFoundError:
            raise ModuleNotFoundError("No matrix client module found, please run j.clients.matrix.install() first")

        self.room = Room(client=self.client, room_id=room_id)

    @room_check
    def send_text(self, text):
        """ Send a plain text message to the room.

        Args:
            text (str): The message to send
        """
        return self.room.send_text(text)

    @room_check
    def send_html(self, html, body=None, msg_type="m.text"):
        """Send an html formatted message."""
        return self.room.send_html(html, body, msg_type)

    @room_check
    def set_account_data(self, account_type, account_data):
        return self.room.set_account_data(account_type, account_data)

    @room_check
    def get_tags(self):
        return self.room.get_tags()

    @room_check
    def remove_tag(self, tag):
        return self.room.remove_tag(tag)

    @room_check
    def add_tag(self, tag, order=None, content=None):
        return self.room.add_tag(tag, order, content)

    @room_check
    def send_emote(self, text):
        """ Send a emote (/me style) message to the room.

        Args:
            text (str): The message to send
        """
        return self.room.send_emote(text)

    @room_check
    def send_notice(self, text):
        return self.client.api.send_notice(self.room.room_id, text)

    @room_check
    def send_image(self, url, name, **imageinfo):
        """ Send a pre-uploaded image to the room.
        See http://matrix.org/docs/spec/r0.0.1/client_server.html#m-image
        for imageinfo

        Args:
            url (str): The mxc url of the image.
            name (str): The filename of the image.
            imageinfo (): Extra information about the image.
        """
        return self.room.send_image(url, name, **imageinfo)

    @room_check
    def send_location(self, geo_uri, name, thumb_url=None, **thumb_info):
        """ Send a location to the room.
        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-location
        for thumb_info

        Args:
            geo_uri (str): The geo uri representing the location.
            name (str): Description for the location.
            thumb_url (str): URL to the thumbnail of the location.
            thumb_info (): Metadata about the thumbnail, type ImageInfo.
        """
        return self.room.send_location(geo_uri, name, thumb_url, **thumb_info)

    @room_check
    def send_video(self, url, name, **videoinfo):
        """ Send a pre-uploaded video to the room.
        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-video
        for videoinfo

        Args:
            url (str): The mxc url of the video.
            name (str): The filename of the video.
            videoinfo (): Extra information about the video.
        """
        return self.room.send_video(url, name, **videoinfo)

    @room_check
    def send_audio(self, url, name, **audioinfo):
        """ Send a pre-uploaded audio to the room.
        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-audio
        for audioinfo

        Args:
            url (str): The mxc url of the audio.
            name (str): The filename of the audio.
            audioinfo (): Extra information about the audio.
        """
        return self.room.send_audio(url, name, **audioinfo)
