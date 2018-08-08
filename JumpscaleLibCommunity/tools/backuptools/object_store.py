class ObjectStore:

    def __init__(self):
        self.type = None

    def __init__(self, stype):
        self.type = stype
        if stype == 'S3':
            self.conn = S3ObjectStore()
        if stype == 'RADOS':
            self.conn = RadosObjectStore()

    def list_pools(self):
        return self.conn.list_pools()

    def list_objects(self, poolname):
        return self.conn.list_objects(poolname)

    def delete_object(self, poolname, key):
        return self.conn.delete_object(poolname, key)

    def get_object(self, poolname, key):
        return self.conn.get_object(poolname, key)

    def create_pool(self, poolname):
        return self.conn.create_pool(poolname)

    def delete_pool(self, poolname):
        return self.conn.delete_pool(poolname)

    def set_object(self, poolname, key, contents):
        return self.conn.set_object(poolname, key, contents)


import boto
from boto.s3.key import Key
from boto.s3 import connection


class S3ObjectStore:
    import boto
    from boto.s3.key import Key
    from boto.s3 import connection

    def connect(self, aws_access_key_id, aws_secret_access_key, host, is_secure, callingformat='ORDINARY'):
        if callingformat == 'ORDINARY':
            calling_format = boto.s3.connection.OrdinaryCallingFormat()
            self.store_connection = boto.connect_s3(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                host=host,
                calling_format=calling_format)
        else:
            self.store_connection = boto.connect_s3(
                aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, host=host)

    def list_pools(self):
        pools = []
        for bucket in self.store_connection.get_all_buckets():
            pools.append(bucket.name)
        return pools

    def create_pool(self, poolname):
        self.store_connection.create_bucket(poolname)
        return poolname

    def delete_pool(self, poolname):
        self.store_connection.delete_bucket(poolname)

    def list_objects(self, poolname):
        bucket = self.store_connection.get_bucket(poolname)
        objects = bucket.list()
        key_names = []
        for obj in objects:
            key_names.append(obj.name)
        return key_names

    def set_object(self, poolname, key, contents):
        bucket = self.store_connection.get_bucket(poolname)
        s3_key = Key(bucket)
        s3_key.key = key
        s3_key.set_contents_from_string(contents)
        return key

    def delete_object(self, poolname, key):
        bucket = self.store_connection.get_bucket(poolname)
        s3_key = bucket.get_key(key)
        s3_key.delete()
        return True

    def get_object(self, poolname, key):
        bucket = self.store_connection.get_bucket(poolname)
        s3_key = bucket.get_key(key)
        content = s3_key.get_contents_as_string()
        return content


#import rados

class RadosObjectStore:

    def connect(self, conffile=''):
        import rados
        self.cluster = rados.Rados(conffile=conffile)
        self.cluster.connect()

    def list_pools(self):
        pools = self.cluster.list_pools()
        return pools

    def create_pool(self, poolname):
        self.cluster.create_pool(poolname)
        return poolname

    def delete_pool(self, poolname):
        self.cluster.delete_pool(poolname)

    def list_objects(self, poolname):
        objects = []
        ioctx = self.cluster.open_ioctx(poolname)
        try:
            object_iterator = ioctx.list_objects()
            for o in object_iterator:
                objects.append(o.key)
        except BaseException:
            raise
        finally:
            ioctx.close()
        return objects

    def set_object(self, poolname, key, contents):
        ioctx = self.cluster.open_ioctx(poolname)
        try:
            ioctx.write_full(key, contents)
        except BaseException:
            raise
        finally:
            ioctx.close()
        return key

    def delete_object(self, poolname, key):
        ioctx = self.cluster.open_ioctx(poolname)
        try:
            ioctx.remove_object(key)
        except BaseException:
            raise
        finally:
            ioctx.close()
        return True

    def get_object(self, poolname, key):
        ioctx = self.cluster.open_ioctx(poolname)
        try:
            content = ioctx.read(key)
        except BaseException:
            raise
        finally:
            ioctx.close()
        return content
