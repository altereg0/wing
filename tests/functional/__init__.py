from unittest import TestCase
from urllib.parse import urlencode
import falcon
from falcon.testing import create_environ, StartResponseMock


class FuncTestCase(TestCase):
    app = None

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

    def check_response(self, resp, status='200 OK'):
        self.assertEqual(status, resp.status, 'Response should be %s' % status)
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')