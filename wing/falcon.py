import falcon
from .serialization import get_serializer


class BaseFalconResource:
    def __init__(self, resource):
        self.resource = resource

    def _check_method(self, method, action):
        if not self.resource.is_method_allowed(method, action):
            raise falcon.HTTPMethodNotAllowed(self.resource.get_allowed_methods(action))


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
        self._check_method('get', 'list')

        result = self.resource.get_list(req, **kwargs)
        serializer = get_serializer(req)
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(result)

    def on_post(self, req, resp, **kwargs):
        """
        Create new object
        :param req: request object
        :param resp: response object
        """
        self._check_method('post', 'list')
        serializer = get_serializer(req)

        req.context['data'] = serializer.loads(req.stream.read().decode('utf-8'))
        result = self.resource.post_list(req, **kwargs)

        resp.status = falcon.HTTP_201
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(result)

    def on_put(self, req, resp, **kwargs):
        self._check_method('put', 'list')
        serializer = get_serializer(req)

        req.context['data'] = serializer.loads(req.stream.read().decode('utf-8'))

        results = self.resource.put_list(req, **kwargs)

        resp.status = falcon.HTTP_200
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(results)

    def on_delete(self, req, resp, **kwargs):
        self._check_method('delete', 'list')

        results = self.resource.delete_list(req, **kwargs)

        resp.status = falcon.HTTP_204
        serializer = get_serializer(req)
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(results)


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
        self._check_method('get', 'details')
        serializer = get_serializer(req)

        result = self.resource.get_details(req, **kwargs)

        resp.status = falcon.HTTP_200
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(result)

    def on_put(self, req, resp, **kwargs):
        """
        Update object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        self._check_method('put', 'details')
        serializer = get_serializer(req)

        req.context['data'] = serializer.loads(req.stream.read().decode('utf-8'))
        result = self.resource.put_details(req, **kwargs)

        resp.status = falcon.HTTP_200
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(result)

    def on_delete(self, req, resp, **kwargs):
        """
        Delete object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        self._check_method('delete', 'details')
        serializer = get_serializer(req)

        result = self.resource.delete_details(req, **kwargs)

        resp.status = falcon.HTTP_204
        resp.content_type = serializer.content_type
        resp.body = serializer.dumps(result)


class FunctionResource():
    pass


def resource_func(func):
    def wrapper(req, resp, *args, **kwargs):
        result = func(req, resp, *args, **kwargs)

        if result is not None:
            serializer = get_serializer(req)
            resp.body = serializer.dumps(result)

    return wrapper


def create_func_resource(func, http_methods):
    resource = FunctionResource()

    for http_method in http_methods:
        method = 'on_' + http_method

        setattr(resource, method, resource_func(func))

    return resource
