from .falcon import ItemFalconResource, CollectionFalconResource, create_func_resource
from .api import Api
from .resources import ModelResource
from . import fields


def register_api(app, api):
    for res in api.resources.values():
        register_resource(app, api.name, res)


def register_resource(app, api_name, resource):
    item_res = ItemFalconResource(resource)
    coll_res = CollectionFalconResource(resource)

    prefix = "/%s/%s" % (api_name, resource._meta.resource_name)

    app.add_route(prefix + '/', coll_res)
    app.add_route(prefix + '/{%s}' % resource._meta.primary_key, item_res)

    for func_name, uri, http_methods in resource.custom_methods:
        func = getattr(resource, func_name)

        custom_res = create_func_resource(func, http_methods)
        app.add_route(prefix + uri, custom_res)
