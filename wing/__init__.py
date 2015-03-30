from .falcon import ItemFalconResource, CollectionFalconResource
from .api import Api
from .resources import ModelResource
from . import fields


def register_api(app, api):
    for name, res in api.resources.items():
        item_res = ItemFalconResource(res)
        coll_res = CollectionFalconResource(res)

        prefix = "/%s/%s" % (api.name, name)

        app.add_route(prefix + '/', coll_res)
        app.add_route(prefix + '/{id}', item_res)
