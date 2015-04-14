from .. import FuncTestCase
import json
from .resources import UserResource
from .models import users, User
import wing

__all__ = ['BasicTests']


class BasicTests(FuncTestCase):
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
        self.check_response(resp, '200 OK')

        objects = json.loads(resp.content)

        self.assertEqual(2, len(objects))

        self.assertEqual('test1', objects[0]['name'])
        self.assertEqual('test2', objects[1]['name'])

    def test_user_details(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/users/1')
        self.check_response(resp, '200 OK')

        user = json.loads(resp.content)

        self.assertEqual('test1', user['name'])
        self.assertEqual(False, user['is_active'])

    def test_user_add(self):
        data = {
            'name': 'test3',
            'is_active': True,
        }
        resp = self.request('POST', '/v1/users/', body=json.dumps(data))
        self.check_response(resp, '201 Created')

        result = json.loads(resp.content)
        self.assertEqual(3, result['pk'])

    def test_user_update(self):
        data = {
            'name': 'test2-updated',
            'is_active': True,
        }
        resp = self.request('PUT', '/v1/users/2', body=json.dumps(data))
        self.check_response(resp, '200 OK')

        user = json.loads(resp.content)

        self.assertEqual('test2-updated', user['name'])
        self.assertEqual(True, user['is_active'])
