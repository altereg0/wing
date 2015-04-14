from .. import FuncTestCase
import json
from .models import User, Category, Post
from .resources import UserResource, CategoryResource, PostResource
import wing

__all__ = ['BasicModelTests', 'RelationsModelTests']


class BasicModelTests(FuncTestCase):
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
        self.check_response(resp, '200 OK')

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
        self.check_response(resp, '200 OK')

        user = json.loads(resp.content)

        self.assertEqual('test1', user['name'])
        self.assertEqual(False, user['is_active'])

    def test_add(self):
        data = {
            'name': 'test3',
            'is_active': True,
        }
        resp = self.request('POST', '/v1/users/', body=json.dumps(data))
        self.check_response(resp, '201 Created')

        result = json.loads(resp.content)
        self.assertEqual(3, result['id'])

    def test_update_details(self):
        data = {
            'name': 'test2-updated',
            'is_active': True,
        }

        resp = self.request('PUT', '/v1/users/2', body=json.dumps(data))
        self.check_response(resp, '200 OK')

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
        self.check_response(resp, '200 OK')

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

        resp = self.request('GET', '/v1/users/2')
        self.assertEqual('404 Not Found', resp.status, 'Response should be 404 Not Found')

    def test_batch_delete(self):
        resp = self.request('DELETE', '/v1/users/')
        self.assertEqual('204 No Content', resp.status, 'Response should be 204 No Content')
        self.assertEqual('', resp.content)

        resp = self.request('GET', '/v1/users/')
        self.check_response(resp, '200 OK')

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

    def test_no_required_field(self):
        data = {
            'is_active': True,
        }
        resp = self.request('POST', '/v1/users/', body=json.dumps(data))
        self.check_response(resp, '400 Bad Request')

        result = json.loads(resp.content)
        self.assertEqual('Validation error', result.get('title'))

    def test_not_json(self):
        resp = self.request('POST', '/v1/users/', body='Invalid JSON')
        self.check_response(resp, '400 Bad Request')

        result = json.loads(resp.content)
        self.assertEqual('Invalid format', result.get('title'))


class RelationsModelTests(FuncTestCase):
    is_safe = False

    @classmethod
    def configure(cls):
        api = wing.Api('v1')
        c_res = CategoryResource()
        p_res = PostResource()
        api.register_resource(c_res)
        api.register_resource(p_res)

        api.register_nested_resource('categories', p_res, 'category')

        wing.register_api(cls.app, api)

    def setUp(self):
        if not self.is_safe:
            Category.drop_table(fail_silently=True)
            Post.drop_table(fail_silently=True)
            Category.create_table()
            Post.create_table()

            c1 = Category(slug="cat1", title="Category #1")
            c1.save()

            c2 = Category(slug="cat2", title="Category #2")
            c2.save()

            Post(slug='post1', title='Post #1').save()
            Post(slug='post2', title='Post #2').save()

            Post(slug='post11', title='Post #11', category=c1).save()
            Post(slug='post12', title='Post #12', category=c1).save()

            Post(slug='post21', title='Post #21', category=c2).save()
            Post(slug='post22', title='Post #22', category=c2).save()

        self.is_safe = False

    def test_post_details(self):
        self.is_safe = True

        resp = self.request('GET', '/v1/posts/1')
        self.check_response(resp, '200 OK')

        post = json.loads(resp.content)

        self.assertEqual('post1', post['slug'])
        self.assertEqual('Post #1', post['title'])
        self.assertEqual(None, post['category'])

    def test_nested_resources(self):
        resp = self.request('GET', '/v1/categories/1/posts/')
        self.check_response(resp, '200 OK')

        data = json.loads(resp.content)

        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 2}, data['meta'])

        objects = data['objects']
        self.assertEqual(2, len(objects))

        self.assertEqual('post11', objects[0]['slug'])
        self.assertEqual('post12', objects[1]['slug'])

    def test_create_nested_resource(self):
        new_post = {
            'slug': 'post-new',
            'title': 'New',
            'category': 2
        }

        resp = self.request('POST', '/v1/categories/1/posts/', body=json.dumps(new_post))
        self.check_response(resp, '201 Created')

        data = json.loads(resp.content)
        self.assertIsNotNone(data.get('id'))

        resp = self.request('GET', '/v1/categories/1/posts/%d' % data.get('id'))
        self.check_response(resp)
        data = json.loads(resp.content)
        self.assertEqual(new_post['slug'], data['slug'])
        self.assertEqual(1, data['category'], 'Category should be rewritten by params from URL')
