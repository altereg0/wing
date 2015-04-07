import json
from tests.func import FuncTestCase
from tests.func.model_resources.resources import CategoryResource, PostResource
from tests.func.model_resources.models import Post, Category
import wing


class TestCase(FuncTestCase):
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
        self._check_response(resp, '200 OK')

        post = json.loads(resp.content)

        self.assertEqual('post1', post['slug'])
        self.assertEqual('Post #1', post['title'])
        self.assertEqual(None, post['category'])

    def test_nested_resources(self):
        resp = self.request('GET', '/v1/categories/1/posts/')
        self._check_response(resp, '200 OK')

        data = json.loads(resp.content)

        self.assertDictEqual({'offset': 0, 'limit': 20, 'total_count': 2}, data['meta'])

        objects = data['objects']
        self.assertEqual(2, len(objects))

        self.assertEqual('post11', objects[0]['slug'])
        self.assertEqual('post12', objects[1]['slug'])

    def _check_response(self, resp, status='200 OK'):
        self.assertEqual(status, resp.status, 'Response should be %s' % status)
        self.assertIn('content-type', resp.headers_dict, 'Content-Type header should return')
        self.assertTrue(resp.headers_dict['content-type'].startswith('application/json'),
                        'Default content type should be application/json')
