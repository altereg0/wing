from unittest import TestCase
from urllib.parse import urlencode
import falcon
from falcon.testing import create_environ, StartResponseMock


class FuncTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = falcon.API()

        conf_func = getattr(cls, 'configure')
        conf_func()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def request(self, method, path, params=None, body=''):
        if not path:
            path = '/'

        if not params:
            params = []

        env = create_environ(path=path, method=method.upper(), query_string=urlencode(params), body=body)

        resp = StartResponseMock()
        result = self.app(env, resp)

        resp.content = ''
        if result:
            resp.content = result[0].decode('utf-8')

        return resp
