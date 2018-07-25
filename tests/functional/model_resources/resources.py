import wing
from .models import *


class UserResource(wing.ModelResource):
    modification_date = wing.fields.DateTimeField('modification_date', required=False)

    class Meta:
        resource_name = 'users'
        filtering = {
            'name': ['exact', 'startswith']
        }
        object_class = User
        primary_key = 'user'


class CategoryResource(wing.ModelResource):
    class Meta:
        resource_name = 'categories'
        object_class = Category
        primary_key = 'category'


class PostResource(wing.ModelResource):
    category = wing.fields.ForeignKeyField('category', CategoryResource)

    class Meta:
        resource_name = 'posts'
        object_class = Post
        primary_key = 'post'
