import json
from tests.func import FuncTestCase
from tests.func.model_resources.resources import UserResource
from tests.func.model_resources.models import User
import wing


class TestCase(FuncTestCase):
    is_safe = False

    @classmethod
    def configure(cls):
        api = wing.Api('v1')
        api.register_resource(UserResource())
        wing.register_api(cls.app, api)

    def setUp(self):
        if not self.is_safe:
            User.drop_table(fail_silently=True)
            User.create_table()
            User(name="test1").save()
            User(name='test2', is_active=True).save()

        self.is_safe = False

    def test_show_list(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/users')
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        data = json.loads(resp.content)

        self.assertDictEqual({
            'offset': 0,
            'limit': 20,
            'total_count': 2
        }, data['meta'])

        objects = data['objects']
        self.assertEqual(2, len(objects))

        self.assertEqual('test1', objects[0]['name'])
        self.assertEqual('test2', objects[1]['name'])

    def test_show_details(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/users/1')

        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        user = json.loads(resp.content)

        self.assertEqual('test1', user['name'])
        self.assertEqual(False, user['is_active'])

    def test_add(self):
        data = {
            'name': 'test3',
            'is_active': True,
        }
        resp = self.request('POST', '/v1/users/', body=json.dumps(data))

        self.assertEqual('201 Created', resp.status, 'Response should be 201 Created')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        result = json.loads(resp.content)
        self.assertEqual(3, result['id'])

    def test_update_details(self):
        data = {
            'name': 'test2-updated',
            'is_active': True,
        }
        resp = self.request('PUT', '/v1/users/2', body=json.dumps(data))

        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        user = json.loads(resp.content)

        self.assertEqual(2, user['id'])
        self.assertEqual('test2-updated', user['name'])
        self.assertEqual(True, user['is_active'])

    def test_batch_update(self):
        data = [{
                    'id': 2,
                    'name': 'test2-updated',
                    'is_active': True,
                },
                {
                    'id': 1,
                    'name': 'test1-updated',
                    'is_active': True,
                }, {
                    'name': 'test3-new',
                    'is_active': True,
                },
        ]
        resp = self.request('PUT', '/v1/users/', body=json.dumps(data))

        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        data = json.loads(resp.content)
        data = data['objects']

        self.assertEqual(3, len(data))

        self.assertEqual('test2-updated', data[0]['name'])
        self.assertEqual('test1-updated', data[1]['name'])
        self.assertEqual('test3-new', data[2]['name'])

    def test_delete(self):
        resp = self.request('DELETE', '/v1/users/2')
        self.assertEqual('204 No Content', resp.status, 'Response should be 204 No Content')
        self.assertEqual('', resp.content)

        resp = self.request('DELETE', '/v1/users/2')
        self.assertEqual('404 Not Found', resp.status, 'Response should be 404 Not Found')

        resp = self.request('GET', '/v1/users/2')
        self.assertEqual('404 Not Found', resp.status, 'Response should be 404 Not Found')

    def test_batch_delete(self):
        resp = self.request('DELETE', '/v1/users/')
        self.assertEqual('204 No Content', resp.status, 'Response should be 204 No Content')
        self.assertEqual('', resp.content)

        resp = self.request('GET', '/v1/users/')
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        data = json.loads(resp.content)

        self.assertDictEqual({
            'offset': 0,
            'limit': 20,
            'total_count': 0
        }, data['meta'])

    def test_wrong_http_method(self):
        resp = self.request('POST', '/v1/users/2')

        self.assertEqual('405 Method Not Allowed', resp.status, 'Response should be 405 Method Not Allowed')
        self.assertIn('allow', resp.headers_dict, 'Allow header should return')

    def test_filtering(self):
        resp = self.request('GET', '/v1/users/', {'name': 'test1'})

        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')

        data = json.loads(resp.content)

        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 1}, data['meta'])

        objects = data['objects']
        self.assertEqual(1, len(objects))

        self.assertEqual('test1', objects[0]['name'])

    def test_custom_filter_type(self):
        resp = self.request('GET', '/v1/users/', {'name__startswith': 'test1'})
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')

        data = json.loads(resp.content)
        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 1}, data['meta'])

        objects = data['objects']
        self.assertEqual(1, len(objects))
        self.assertEqual('test1', objects[0]['name'])

        resp = self.request('GET', '/v1/users/', {'name__startswith': 'est1'})
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')

        data = json.loads(resp.content)
        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 0}, data['meta'])

        objects = data['objects']
        self.assertEqual(0, len(objects))

    def test_not_allowed_filtering(self):
        self.is_safe = True
        resp = self.request('GET', '/v1/users/', {'name__endswith': 'test1'})
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')

        data = json.loads(resp.content)
        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 2}, data['meta'])

        objects = data['objects']
        self.assertEqual(2, len(objects))

