from datetime import datetime
import falcon


class HTTPCache:
    def __init__(self, cache):
        self.cache = cache

    def process_request(self, req, resp):
        if req.method != 'get':
            self.cache.set('last_modify_date', datetime.now())

        if self.check_modified(req):
            req.context['cached'] = True
            resp.status = falcon.HTTP_304
            return


    def check_modified(self, req):
        last_modify_date = self.cache.get('last_modify_date')
        modified_since = req.headers.get('If-Modified-Since')

        return last_modify_date < modified_since

    def check_etag(self, req):
        pass