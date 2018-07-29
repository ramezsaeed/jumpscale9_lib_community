from js9 import j
    
from wordpress_json import WordpressJsonWrapper

# this client requires wordpress configurations
# please follow these instructions https://github.com/stylight/python-wordpress-json

JSConfigBase = j.tools.configmanager.base_class_config

TEMPLATE = """
url = ""
username = ""
password_ = ""
"""
class WordpressClient(JSConfigBase):
    def __init__(self, instance, data={}, parent=None, interactive=None):
        JSConfigBase.__init__(self, instance=instance,
                              data=data, parent=parent, template=TEMPLATE)
        c = self.config.data
        self.url = c["url"]
        self.username = c["username"]
        self.password = c["password_"]
        self._api = None

    def install(self):
        j.tools.prefab.local.runtimes.pip.install("wordpress-json")
    
    @property
    def api(self):
        if not self._api:
            api_url = self.url + "/?rest_route=/wp/v2"
            self.logger.debug("api_url:%s"%api_url)
            self._api = WordpressJsonWrapper(api_url, self.username, self.password)
        return self._api
    
    def users_get(self, id=None):
        """get user or list users if no id provided
        
        Keyword Arguments:
            id {integer} -- user id, if none will return all users (default: {None})
        
        Returns:
            {dict} -- dict representation of users
        """

        if id:
            return self.api.get_user(user_id=id)

        return self.api.get_users()

    def user_create(self, username, email, password, **kwargs):
        """create a user
        
        Arguments:
            username {string} -- username
            email {string } -- email
            password {string} -- password
            **kwargs  -- additional user data
        """

        data = {
            "username": username,
            "email": email,
            "password": password
        }
        data.update(kwargs)
        return self.api.create_user(data=data)
    
    def user_delete(self, id, reassign_id):
        """delete user
        
        Arguments:
            id {integer} -- user id
            reassign_id {integer} -- Reassign the deleted user's posts and links to this user ID
        """

        self.api.delete_user(user_id=id, params={"reassign":reassign_id, "force":True})
    
    def pages_get(self, id=None):
        """get page or list pages if id provided
        
        Arguments:
            id {integer} -- page id
        
        Returns:
            dict -- dict representation of pages
        """

        if id:
            return self.api.get_pages(page_id=id)

        return self.api.get_pages()

    def page_create(self, publish=False, **kwargs):
        """create a page

        Keyword Arguments:
            publish {boolean} -- if true the page will be published after being created (default: {False})
            kwargs -- this should contain all page's data
        """

        data ={}
        if publish:
            data['status'] = 'publish'
        data.update(kwargs)
        return self.api.create_pages(data=data)
    
    def page_delete(self, id):
        """delete page
        
        Arguments:
            id {integer} -- page id to be deleted
        """     

        self.api.delete_pages(page_id= id)

    def posts_get(self, id=None):
        """get post or list post if id provided
        
        Keyword Arguments:
            id {integer} -- post id (default: {None})
        
        Returns:
            dict -- dict representation of post
        """

        if id:
            return self.api.get_post(post_id=id)

        return self.api.get_posts()

    def post_create(self, publish=False, **kwargs):
        """creates a post
        
        Keyword Arguments:
            publish {boolean} -- if true the post will be published once created (default: {False})
        """

        data ={}
        if publish:
            data['status'] = 'publish'
        data.update(kwargs)
        return self.api.create_post(data=data)
    
    def post_delete(self, id):
        """deletes a post
        
        Arguments:
            id {integer} -- post id to be deleted
        """

        self.api.delete_post(post_id=id)