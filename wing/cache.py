from datetime import datetime


class DummyCache:
    def add(self, key, val, ttl=None):
        pass

    def set(self, key, val, ttl=None):
        pass

    def get(self, key):
        return None

    def has(self, key):
        return False

    def remove(self, key):
        pass

    def clear(self):
        pass


class LocMemCache:
    def __init__(self):
        self.data = {}

    def add(self, key, val, ttl=None):
        if self.has(key):
            return False

        self.set(key, val, ttl)

        return True

    def set(self, key, val, ttl=None):
        expire_ts = datetime.now().timestamp() + ttl if ttl is not None else None
        self.data[key] = (val, expire_ts)

    def get(self, key):
        val, expire = self.data.get(key, (None, None))

        if expire is not None and expire > datetime.now().timestamp():
            del self.data[key]
            return None

        return val

    def has(self, key):
        val, expire = self.data.get(key, (None, None))

        return expire and expire < datetime.now().timestamp()

    def remove(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass

    def clear(self):
        self.data = {}


try:
    import redis

    class RedisCache:
        def __init__(self, client, prefix=''):
            self.client = client
            self.prefix = prefix

        def add(self, key, val, ttl=None):
            ttl = ttl * 1000 if ttl else None
            self.client.set(self.prefix + key, val, px=ttl, nx=True)

        def set(self, key, val, ttl=None):
            self.client.set(self.prefix + key, val, px=ttl * 1000)

        def get(self, key):
            return self.client.get(self.prefix + key)

        def has(self, key):
            return self.client.get(self.prefix + key) is not None

        def remove(self, key):
            self.client.delete(self.prefix + key)

        def clear(self):
            self.client.flushdb()

except ImportError:
    pass
