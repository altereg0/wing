from .. import settings


def get_serializer(req):
    type = settings.SERIALIZER_DEFAULT

    if settings.SERIALIZER_REQUEST_PARAM:
        type = req.get_param(settings.SERIALIZER_REQUEST_PARAM) or type

    return _get_serializer_by_type(type)


def _get_serializer_by_type(type):
    if type == 'json':
        from . import json

        return json
    elif type == 'yaml':
        from . import yaml

        return yaml

    raise NotImplemented