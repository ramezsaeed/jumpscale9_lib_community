from js9 import j

from .WordpressClient import WordpressClient

JSConfigBase = j.tools.configmanager.base_class_configs


class WordpressFactory(JSConfigBase):

    def __init__(self):
        self.__jslocation__ = "j.clients.wordpress"
        JSConfigBase.__init__(self, WordpressClient)

    def test(self):
        """
        js9 'j.clients.wordpress.test()'
        """
        wp_cl = j.clients.wordpress.get('test')

        # test posts 
        current_posts_count = len(wp_cl.posts_get())
        new_post = wp_cl.post_create(publish=True, title="test post")
        assert len(wp_cl.posts_get()) == current_posts_count + 1
        wp_cl.post_delete(id=new_post['id'])
        assert len(wp_cl.posts_get()) == current_posts_count

        # test pagess 
        current_pages_count = len(wp_cl.pages_get())
        new_page = wp_cl.page_create(publish=True, title="test page")
        assert len(wp_cl.pages_get()) == current_pages_count + 1
        wp_cl.page_delete(id=new_page['id'])
        assert len(wp_cl.pages_get()) == current_pages_count

        # test user 
        current_users_count = len(wp_cl.users_get())
        new_user = wp_cl.user_create(username="test_user", password="test_password", email="test@a.grid.tf")
        assert len(wp_cl.users_get()) == current_users_count + 1
        wp_cl.user_delete(new_user['id'], 1)
        assert len(wp_cl.users_get()) == current_users_count

        print("Success")



        