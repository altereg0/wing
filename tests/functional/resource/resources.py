import falcon
from .models import User, users
import wing


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
