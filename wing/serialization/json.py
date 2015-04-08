from datetime import datetime
import json

content_type = 'application/json'


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)


def dumps(obj):
    return json.dumps(obj, cls=JSONEncoder)


def loads(content):
    return json.loads(content)
