from copy import copy
from .fields import Field
from .adapters import detect_adapter
from .errors import DoesNotExist, MissingRequiredFieldError, NotNullFieldError, FieldValidationError, IntegrityError
import falcon
from .settings import DEFAULT_MAX_LIMIT, DEFAULT_LIMIT


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


class ResourceOptions(object):
    allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
    list_allowed_methods = None
    details_allowed_methods = None
    limit = DEFAULT_LIMIT
    max_limit = DEFAULT_MAX_LIMIT
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

        allowed_methods = overrides.get('allowed_methods', ResourceOptions.allowed_methods)

        if overrides.get('list_allowed_methods', None) is None:
            overrides['list_allowed_methods'] = allowed_methods

        if overrides.get('details_allowed_methods', None) is None:
            overrides['details_allowed_methods'] = allowed_methods

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

            new_class.fields.update(new_class._db.get_fields(new_class._meta.excludes + list(new_class.fields.keys())))

        return new_class


class Resource(metaclass=DeclarativeMetaclass):
    _meta = None

    fields = None

    def is_method_allowed(self, method, action):
        return method in self.get_allowed_methods(action)

    def get_allowed_methods(self, action):
        if action == 'list':
            return self._meta.list_allowed_methods
        elif action == 'details':
            return self._meta.details_allowed_methods
        else:
            return self._meta.allowed_methods

    def get_list(self, req, **kwargs):
        raise NotImplemented

    def post_list(self, req, **kwargs):
        raise NotImplemented

    def put_list(self, req, **kwargs):
        raise NotImplemented

    def delete_list(self, req, **kwargs):
        raise NotImplemented

    def get_details(self, req, **kwargs):
        raise NotImplemented

    def put_details(self, req, **kwargs):
        raise NotImplemented

    def delete_details(self, req, **kwargs):
        raise NotImplemented

    def dehydrate(self, obj, sender=None):
        """
        Dehydrate object
        :param obj: object
        """
        return {key: field.dehydrate(obj) for key, field in self.fields.items() if
                sender is None or (sender in field.show)}

    def hydrate(self, obj, data):
        """
        Hydrate data to object
        :param obj: object
        :param data: data as dictionary
        """
        for key, field in self.fields.items():
            if field.readonly:
                continue

            if key not in data:
                if field.required:
                    raise MissingRequiredFieldError(key)

                continue

            value = data.get(key, None)

            if not field.null and value is None:
                raise NotNullFieldError(key)

            field.hydrate(obj, value)

    @classmethod
    def _filters_from_request(cls, req):
        filters = []
        for key, v in req.params.items():
            try:
                field, op = key.rsplit('__', 1)
            except Exception:
                field, op = key, 'exact'

            if field in cls._meta.filtering and op in cls._meta.filtering[field]:
                filters.append((field, op, v))

        return filters

    @classmethod
    def _filters_from_kwargs(cls, **kwargs):
        return [(k, 'exact', cls.fields[k].convert(v)) for k, v in kwargs.items()]


class ModelResource(Resource, metaclass=ModelDeclarativeMetaclass):
    _db = None

    def get_list(self, req, **kwargs):
        try:
            filters = self._filters_from_request(req) + self._filters_from_kwargs(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        offset = req.get_param_as_int('offset', min=0) or 0
        limit = req.get_param_as_int('limit', min=1, max=self._meta.max_limit) or self._meta.limit

        qs = self._db.select(filters)
        meta, qs = self._paginate(qs, offset, limit)

        return {
            'meta': meta,
            'objects': [self.dehydrate(obj, sender='list') for obj in qs]
        }

    def post_list(self, req, **kwargs):
        data = copy(req.context['data'])
        data.update(kwargs)

        obj = self._db.create_object()

        try:
            self.hydrate(obj, data)
        except FieldValidationError as e:
            raise falcon.HTTPBadRequest('Bad request', str(e))

        self.save_obj(obj)

        return {
            self._meta.primary_key: getattr(obj, self._meta.primary_key)
        }

    def delete_list(self, req, **kwargs):
        try:
            filters = self._filters_from_request(req) + self._filters_from_kwargs(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        self._db.delete(filters)

    def put_list(self, req, **kwargs):
        data = req.context['data']

        for k, v in kwargs:
            try:
                self.fields[k].convert(v)
            except DoesNotExist:
                raise falcon.HTTPNotFound()

        pk_field = self._meta.primary_key

        results = []
        for item in data:
            pk = item.get(pk_field)
            item.update(kwargs)

            if not pk:
                obj = self._db.create_object()
            else:
                params = copy(kwargs)
                params[pk_field] = pk

                try:
                    obj = self.find_object(**params)
                except DoesNotExist:
                    raise falcon.HTTPBadRequest('Object not found', 'Object with primary key "%s" not found' % pk)

            self.hydrate(obj, item)

            self.save_obj(obj)

            results.append(self.dehydrate(obj, sender='list'))

        return {
            'objects': results
        }

    def get_details(self, req, **kwargs):
        try:
            obj = self.find_object(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        return self.dehydrate(obj, sender='details')

    def put_details(self, req, **kwargs):
        try:
            obj = self.find_object(**kwargs)
        except DoesNotExist:
            raise falcon.HTTPNotFound()

        data = req.context['data']

        self.hydrate(obj, data)
        self.save_obj(obj)

        return self.dehydrate(obj, sender='details')

    def delete_details(self, req, **kwargs):
        affected_rows = self._db.delete(self._filters_from_kwargs(**kwargs))

        if not affected_rows:
            raise falcon.HTTPNotFound()

    def find_object(self, **kwargs):
        qs = self._db.select(self._filters_from_kwargs(**kwargs))[:1]

        if len(qs) == 0:
            raise DoesNotExist()

        return qs[0]

    def save_obj(self, obj):
        try:
            self._db.save_object(obj)
        except IntegrityError as e:
            raise falcon.HTTPBadRequest('Integrity error', *e.args[0])

    def _paginate(self, qs, offset, limit):
        meta = {
            'limit': limit,
            'offset': offset,
            'total_count': qs.count(),  # todo: make it using db adapter
        }

        return meta, qs[offset:offset + limit]
