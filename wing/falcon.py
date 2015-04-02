import falcon
from . import serialization
from .errors import DoesNotExist


class BaseFalconResource:
    def __init__(self, resource):
        self.resource = resource


class CollectionFalconResource(BaseFalconResource):
    """
    Objects collection base resource
    """

    def on_get(self, req, resp, **kwargs):
        """
        Get objects list
        :param req: request object
        :param resp: response object
        """
        if 'get' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

        filters = self._get_filters(req)

        qs = self.resource.get_object_list(filters, **kwargs)
        resp.body = serialization.dumps(self.resource.paginate(req, qs))

    def on_post(self, req, resp):
        """
        Create new object
        :param req: request object
        :param resp: response object
        """
        if 'post' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

        data = serialization.loads(req.stream.read().decode('utf-8'))

        obj = self.resource.create_object()
        self.resource.hydrate(obj, data, req)
        obj.save()

        resp.status = falcon.HTTP_201
        resp.body = serialization.dumps({
            self.resource._meta.primary_key: obj.id
        })

    def on_put(self, req, resp):
        if 'put' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

        data = serialization.loads(req.stream.read().decode('utf-8'))

        results = []

        pk_field = self.resource._meta.primary_key

        for item in data:
            pk = item.get(pk_field)

            if not pk:
                raise falcon.HTTPBadRequest('No PK', 'Object primary key not found')

            try:
                obj = self.resource.get_object(**{pk_field: pk})
            except DoesNotExist:
                raise falcon.HTTPNotFound()

            self.resource.hydrate(obj, item, req)

            obj.save()

            results.append({pk_field: obj.id})

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(results)

    def _get_filters(self, req):
        filters = []
        for key, v in req.params.items():
            try:
                field, op = key.rsplit('__', 1)
            except Exception:
                field, op = key, 'exact'

            if field in self.resource._meta.filtering and op in self.resource._meta.filtering[field]:
                filters.append((field, op, v))

        return filters


class ItemFalconResource(BaseFalconResource):
    """
    Object item base resource
    """

    def on_get(self, req, resp, **kwargs):
        """
        Show object details
        :param pk: object id
        :param req: request object
        :param resp: response object
        """

        if 'get' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

        try:
            obj = self.resource.get_object(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(self.resource.dehydrate(obj, req, sender='details'))

    def on_put(self, req, resp, **kwargs):
        """
        Update object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        if 'put' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

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
        if 'delete' not in self.resource._meta.allowed_methods:
            raise falcon.HTTPMethodNotAllowed(self.resource._meta.allowed_methods)

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
