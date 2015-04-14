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
