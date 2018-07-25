from collections import defaultdict

from falcon.api_helpers import prepare_middleware

from wing.falcon.middlewares import HTTPCache
from .falcon.resources import ItemFalconResource, CollectionFalconResource, create_func_resource


class Api:
    def __init__(self, api_name):
        self.name = api_name
        self.resources = {}
        self.nested = defaultdict(list)

    def register_resource(self, resource):
        self.resources[resource._meta.resource_name] = resource

    def register_nested_resource(self, nested_resource_name, resource, foreign_key):
        if nested_resource_name not in self.resources:
            raise Exception()

        self.nested[nested_resource_name].append((resource, foreign_key))


def register_api(app, api):
    prefix = '/' + api.name
    for res in api.resources.values():
        register_resource(app, prefix, res)

    for res_name, nested_resources in api.nested.items():
        for nested_resource, foreign_key in nested_resources:
            register_resource(
                app,
                prefix + '/{:s}/{{{:s}}}'.format(api.resources[res_name]._meta.resource_name, foreign_key),
                nested_resource
            )


def register_resource(app, prefix, resource):
    item_res = ItemFalconResource(resource)
    coll_res = CollectionFalconResource(resource)

    prefix += "/{:s}".format(resource._meta.resource_name)

    app.add_route(prefix, coll_res)
    app.add_route(prefix + '/{{{:s}}}'.format(resource._meta.primary_key), item_res)

    for func_name, uri, http_methods in resource.custom_methods:
        func = getattr(resource, func_name)

        custom_res = create_func_resource(func, http_methods)
        app.add_route(prefix + uri, custom_res)

    if resource._meta.http_cache and resource._meta.cache:
        middleware = HTTPCache(resource._meta.cache, resource)
        app._middleware.extend(prepare_middleware([middleware]))
