from .fields import Field
from .adapters import detect_adapter
from .errors import DoesNotExist


class ResourceOptions(object):
    allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
    limit = 20
    max_limit = 1000
    resource_name = None
    filtering = {}
    ordering = []
    object_class = None
    excludes = []
    primary_key = 'id'
    adapter = None

    def __new__(cls, meta=None):
        overrides = {}

        # Handle overrides.
        if meta:
            for override_name in dir(meta):
                # No internals please.
                if not override_name.startswith('_'):
                    overrides[override_name] = getattr(meta, override_name)

        return object.__new__(type('ResourceOptions', (cls,), overrides))


class DeclarativeMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(DeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)

        opts = getattr(new_class, 'Meta', None)
        new_class._meta = ResourceOptions(opts)

        new_class.fields = {}
        for field_name, obj in attrs.copy().items():
            if isinstance(obj, Field):
                new_class.fields[field_name] = attrs.pop(field_name)

        new_class.custom_methods = []
        for func_name, func in attrs.items():
            func_uri = getattr(func, 'uri', None)
            func_http_methods = getattr(func, 'http_methods', None)

            if getattr(func, 'type', None) is not None:
                new_class.custom_methods.append((func_name, func_uri, func_http_methods))

        return new_class


class ModelDeclarativeMetaclass(DeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(ModelDeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)

        if new_class._meta.object_class:
            if not new_class._meta.adapter:
                new_class._meta.adapter = detect_adapter(new_class._meta.object_class)

            new_class._db = new_class._meta.adapter(new_class._meta.object_class)

            new_class.fields = new_class._db.get_fields(new_class._meta.excludes + list(new_class.fields.keys()))

        return new_class


class ModelResource(metaclass=ModelDeclarativeMetaclass):
    _db = None
    _meta = None

    fields = None

    def get_object_list(self, filters=None, **kwargs):
        if not filters:
            filters = []

        return self._db.select(filters + self._make_filters_from_kwargs(**kwargs))

    def get_object(self, **kwargs):
        qs = self._db.select(self._make_filters_from_kwargs(**kwargs))[:1]

        if len(qs) == 0:
            raise DoesNotExist()

        return qs[0]

    def create_object(self):
        return self._db.create_object()

    def delete_object(self, **kwargs):
        return self._db.delete(self._make_filters_from_kwargs(**kwargs))

    def dehydrate(self, obj, req, sender=None):
        """
        Dehydrate object
        :param obj: object
        """
        return {key: field.dehydrate(obj) for key, field in self.fields.items() if
                sender is None or (sender in field.show)}

    def hydrate(self, obj, data, req):
        """
        Hydrate data to object
        :param obj: object
        :param data: data as dictionary
        """
        for key, field in self.fields.items():
            if field.readonly:
                continue

            if key not in data:
                continue

            value = data.get(key, None)

            field.hydrate(obj, value)

    def paginate(self, req, query):
        """
        Paginate object using request
        :param req: request
        """
        page = req.get_param_as_int('page', min=1) or 1

        limit = req.get_param_as_int('limit', min=1, max=self._meta.max_limit) or self._meta.limit
        offset = (page - 1) * limit

        return {
            'meta': {
                'limit': limit,
                'offset': (page - 1) * limit,
                'total_count': query.count(),
            },

            'objects': [self.dehydrate(item, req, sender='list') for item in query[offset:offset + limit]]
        }

    def _make_filters_from_kwargs(self, **kwargs):
        return [(k, 'exact', self.fields[k].convert(v)) for k, v in kwargs.items()]


def custom_method(uri, http_methods=None):
    if not http_methods:
        http_methods = ['get']

    if isinstance(http_methods, str):
        http_methods = [http_methods]

    def wrapper(func):
        func.type = 'custom'
        func.uri = uri
        func.http_methods = http_methods
        return func

    return wrapper
