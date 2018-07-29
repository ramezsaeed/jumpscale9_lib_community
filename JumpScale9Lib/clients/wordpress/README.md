# How to use the JumpScale Client for Wordpress

First make sure `wordpress_json` is installed:
```bash
pip install wordpress_json
```

If not already the case, create a new configuration instance for your Wordpress site:
```python
wp_url = "http://wp1.b.grid.tf"
wp_admin_username = "****"
wp_admin_password = "****"

wp_config = {
    "username": wp_admin_username,
    "password_": wp_admin_password,
    "url": wp_url 
}

wp_instance_name = "wp1"
wp_cl = j.clients.wordpress.get(instance=wp_instance_name, data=wp_config, create=True, die=True, interactive=False)
```

Once you have a Wordpress configuration instance, connecting to your Wordpress site is easy:
```python
wp_cl = j.clients.wordpress.get(instance=wp_instance_name)
```

Example code in order to work with post:
```python
current_posts_count = len(wp_cl.posts_get())
new_post = wp_cl.post_create(publish=True, title="test post")
assert len(wp_cl.posts_get()) == current_posts_count + 1
wp_cl.post_delete(id=new_post['id'])
assert len(wp_cl.posts_get()) == current_posts_count
```

Example code in order to work with pages:
```python
current_pages_count = len(wp_cl.pages_get())
new_page = wp_cl.page_create(publish=True, title="test page")
new_page = wp_cl.page_create(publish=True, title="test page2")
assert len(wp_cl.pages_get()) == current_pages_count + 1
wp_cl.page_delete(id=new_page['id'])
assert len(wp_cl.pages_get()) == current_pages_count
```

Example code in order to work with users:
```python
current_users_count = len(wp_cl.users_get())
new_user = wp_cl.user_create(username="test_user", password="test_password", email="test.b.grid.tf")
assert len(wp_cl.users_get()) == current_users_count + 1
wp_cl.user_delete(new_user['id'], reassign_id=1)
assert len(wp_cl.users_get()) == current_users_count
```
