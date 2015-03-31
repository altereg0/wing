import falcon
from . import serialization
from peewee import DoesNotExist
from .pagination import Paginator


class BaseFalconResource:
    def __init__(self, resource):
        self.resource = resource


class CollectionFalconResource(BaseFalconResource):
    """
    Objects collection base resource
    """

    def on_get(self, req, resp):
        """
        Get objects list
        :param req: request object
        :param resp: response object
        """
        query_set = self.resource.get_object_list()

        p = Paginator(query_set, 20)
        p.page_number = req.get_param_as_int('page', min=1) or 1

        result = {
            'meta': {
                'limit': 20,
                'offset': p.offset,
                'total_count': p.total_count,
            },

            'objects': [self.resource.dehydrate(item, req) for item in p.items]
        }

        resp.body = serialization.dumps(result)

    def on_post(self, req, resp):
        """
        Create new object
        :param req: request object
        :param resp: response object
        """
        data = serialization.loads(req.stream.read().decode('utf-8'))

        obj = self.resource.create_object()
        self.resource.hydrate(obj, data, req)
        obj.save()

        resp.status = falcon.HTTP_201
        resp.body = serialization.dumps({
            self.resource._meta.primary_key: obj.id
        })


class ItemFalconResource(BaseFalconResource):
    """
    Object item base resource
    """

    def on_get(self, req, resp, **kwargs):
        """
        Show object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        try:
            obj = self.resource.get_object(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(self.resource.dehydrate(obj, req))

    def on_put(self, req, resp, **kwargs):
        """
        Update object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        try:
            obj = self.resource.get_object(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        data = serialization.loads(req.stream.read().decode('utf-8'))
        self.resource.hydrate(obj, data, req)
        obj.save()

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(self.resource.dehydrate(obj, req))

    def on_delete(self, req, resp, **kwargs):
        """
        Delete object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        affected_rows = self.resource.delete_object(**kwargs)

        resp.status = falcon.HTTP_204 if affected_rows > 0 else falcon.HTTP_404


class FunctionResource():
    pass


def resource_func(func):
    def wrapper(req, resp, *args, **kwargs):
        result = func(req, resp, *args, **kwargs)

        if result is not None:
            resp.body = serialization.dumps(result)

    return wrapper


def create_func_resource(func, http_methods):
    resource = FunctionResource()

    for http_method in http_methods:
        method = 'on_' + http_method

        setattr(resource, method, resource_func(func))

    return resource
