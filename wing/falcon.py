import falcon
from . import serialization
from peewee import DoesNotExist
from .pagination import Paginator


class BaseFalconResource:
    def __init__(self, resource):
        self.resource = resource

    def dehydrate_list(self, objects, req):
        """
        Dehydrate object list
        :param objects: object list
        """
        return [self.dehydrate(obj, req) for obj in objects]

    def dehydrate(self, obj, req):
        """
        Dehydrate object
        :param obj: object
        :param fields: visible fields, all by default
        """
        return self.resource.dehydrate(obj, req)

    def hydrate(self, obj, data, req):
        """
        Hydrate data to object
        :param obj: object
        :param data: data as dictionary
        """
        self.hydrate(obj, data, req)


class CollectionFalconResource(BaseFalconResource):
    """
    Objects collection base resource
    """

    def get_object_list(self, req):
        """
        Get object collection as query set or list
        :param req:
        :return: objects list
        """
        return self.resource.get_object_list()

    def make_object(self, req):
        """
        Make new object
        This method shouldn't save object.
        :param req: request
        """
        return self.resource.create_object()

    def on_get(self, req, resp):
        """
        Get objects list
        :param req: request object
        :param resp: response object
        """
        query_set = self.get_object_list(req)

        p = Paginator(query_set, 20)
        p.page_number = req.get_param_as_int('page', min=1) or 1

        result = {
            'meta': {
                'limit': 20,
                'offset': p.offset,
                'total_count': p.total_count,
            },

            'objects': self.dehydrate_list(p.items, req)
        }

        resp.body = serialization.dumps(result)

    def on_post(self, req, resp):
        """
        Create new object
        :param req: request object
        :param resp: response object
        """
        data = serialization.loads(req.stream.read().decode('utf-8'))

        obj = self.make_object(req)
        self.hydrate(obj, data, req)
        obj.save()

        resp.status = falcon.HTTP_201
        resp.body = serialization.dumps({
            'id': obj.id
        })


class ItemFalconResource(BaseFalconResource):
    """
    Object item base resource
    """

    def get_object(self, id, req):
        """
        Get object by primary key
        :param pk: primary key (string)
        :param req: request
        :return: object
        """
        try:
            return self.resource.get_object(id=id)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

    def delete_object(self, id, req):
        """
        Delete object by primary key and return affected rows - 1 or 0
        :param pk: primary key
        :param req: request
        :return: affected rows
        """
        return self.resource.delete_object(id=id)

    def on_get(self, req, resp, id):
        """
        Show object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        obj = self.get_object(id, req)

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(self.dehydrate(obj, req))

    def on_put(self, req, resp, id):
        """
        Update object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        obj = self.get_object(id, req)

        data = serialization.loads(req.stream.read().decode('utf-8'))
        obj = self.hydrate(obj, data, req)
        obj.save()

        resp.status = falcon.HTTP_200
        resp.body = serialization.dumps(self.dehydrate(obj, req))

    def on_delete(self, req, resp, id):
        """
        Delete object
        :param pk: object id
        :param req: request object
        :param resp: response object
        """
        affected_rows = self.delete_object(id, req)

        resp.status = falcon.HTTP_204 if affected_rows > 0 else falcon.HTTP_404
