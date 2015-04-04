import json
import falcon
from tests.func import FuncTestCase
import wing


class User(object):
    def __init__(self, name='', is_active=False):
        self.name = name
        self.is_active = is_active


users = []


class UserResource(wing.Resource):
    name = wing.fields.CharField('name')
    is_active = wing.fields.BooleanField('is_active')

    def get_list(self, req, **kwargs):
        return [self.dehydrate(obj, sender='list') for obj in users]

    def post_list(self, req, **kwargs):
        user = User()

        self.hydrate(user, req.context['data'])

        users.append(user)

        return {
            'pk': len(users)
        }

    def get_details(self, req, **kwargs):
        try:
            user = users[int(kwargs['pk']) - 1]
        except KeyError:
            raise falcon.HTTPNotFound()

        return self.dehydrate(user, sender='details')

    def put_details(self, req, **kwargs):
        try:
            user = users[int(kwargs['pk']) - 1]
        except KeyError:
            raise falcon.HTTPNotFound()

        self.hydrate(user, req.context['data'])

        return self.dehydrate(user, sender='details')

    class Meta:
        resource_name = 'users'
        object_class = User
        primary_key = 'pk'


class AppTestCase(FuncTestCase):
    is_safe = False

    @classmethod
    def configure(cls):
        api = wing.Api('v1')
        api.register_resource(UserResource())
        wing.register_api(cls.app, api)

    def setUp(self):
        if not self.is_safe:
            users.clear()
            users.append(User('test1', False))
            users.append(User('test2', True))

        self.is_safe = False

    def test_users_list(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/users')
        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        objects = json.loads(resp.content)

        self.assertEqual(2, len(objects))

        self.assertEqual('test1', objects[0]['name'])
        self.assertEqual('test2', objects[1]['name'])

    def test_user_details(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/users/1')

        self.assertEqual('200 OK', resp.status, 'Response should be 200 OK')
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')

        user = json.loads(resp.content)

        self.assertEqual('test1', user['name'])
        self.assertEqual(False, user['is_active'])

    def test_user_add(self):
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
        self.assertEqual(3, result['pk'])

    def test_user_update(self):
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

        self.assertEqual('test2-updated', user['name'])
        self.assertEqual(True, user['is_active'])
