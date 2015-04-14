from datetime import datetime
import hashlib
from .errors import HTTPNotModified


def md5_hash(s):
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()


class HTTPCache:
    CACHE_KEY = 'http_last_modify_date'

    def __init__(self, cache, resource):
        self.cache = cache
        self.resource = resource

        self.cache.add(self.CACHE_KEY, datetime.utcnow())

    def process_resource(self, req, resp, res):
        if res is None or getattr(res, 'resource', None) is not self.resource:
            return

        if req.method.lower() != 'get':
            self.cache.set(self.CACHE_KEY, datetime.utcnow())
            return

        last_modify_date = self.get_last_modify_date()
        etag = self.get_etag(req)

        if req.if_modified_since:
            modified_since = datetime.strptime(req.if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
        else:
            modified_since = None

        req_etag = req.if_none_match

        resp.etag = etag
        resp.last_modified = last_modify_date

        if (last_modify_date and modified_since and last_modify_date < modified_since) or (req_etag == etag):
            raise HTTPNotModified()

    def get_last_modify_date(self):
        return self.cache.get(self.CACHE_KEY)

    def get_etag(self, req):
        last_modify_date = self.cache.get(self.CACHE_KEY)

        return md5_hash(last_modify_date.strftime('%Y-%m-%d %H:%M:%S') + req.path + req.query_string)
