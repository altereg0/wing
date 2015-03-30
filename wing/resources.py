from .fields import Field, create_resource_field


def get_fields_from_cls(cls, excludes=None):
    """
    Get fields for ORM model class
    :param cls: model class
    """
    fields = {}
    if not excludes: excludes = []

    for key, field in cls._meta.fields.items():
        if key not in excludes:
            fields[key] = create_resource_field(field)

    return fields


class ResourceOptions(object):
    allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
    list_allowed_methods = None
    detail_allowed_methods = None
    limit = 20
    max_limit = 1000
    resource_name = None
    filtering = {}
    ordering = []
    object_class = None
    queryset = None
    excludes = []
    primary_key = 'id'

    def __new__(cls, meta=None):
        overrides = {}

        # Handle overrides.
        if meta:
            for override_name in dir(meta):
                # No internals please.
                if not override_name.startswith('_'):
                    overrides[override_name] = getattr(meta, override_name)

        allowed_methods = overrides.get('allowed_methods', ['get', 'post', 'put', 'delete', 'patch'])

        if overrides.get('list_allowed_methods', None) is None:
            overrides['list_allowed_methods'] = allowed_methods

        if overrides.get('detail_allowed_methods', None) is None:
            overrides['detail_allowed_methods'] = allowed_methods

        return object.__new__(type('ResourceOptions', (cls,), overrides))


class ModelDeclarativeMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(ModelDeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)
        opts = getattr(new_class, 'Meta', None)
        new_class._meta = ResourceOptions(opts)

        if new_class._meta.object_class:
            fields = get_fields_from_cls(new_class._meta.object_class, new_class._meta.excludes)

            for field_name, obj in attrs.copy().items():
                if isinstance(obj, Field):
                    fields[field_name] = attrs.pop(field_name)

            new_class.fields = fields

        return new_class


class ModelResource(metaclass=ModelDeclarativeMetaclass):
    def get_object_list(self, **kwargs):
        return self.apply_filters(self._meta.queryset, kwargs)

    def get_object(self, **kwargs):
        cls = self._meta.object_class

        objects = self.apply_filters(self._meta.queryset, kwargs)
        objects = objects[:1]

        if len(objects) == 0:
            raise cls.DoesNotExist()

        return objects[0]

    def create_object(self):
        return self._meta.object_class()

    def delete_object(self, **kwargs):
        objects = self.apply_filters(self._meta.queryset, kwargs)
        return objects.delete().execute()

    def dehydrate(self, obj, req):
        """
        Dehydrate object
        :param obj: object
        :param fields: visible fields, all by default
        """
        return {key: field.dehydrate(obj) for key, field in self.fields.items()}

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

    def apply_filters(self, query, filters):
        cls = self._meta.object_class

        conditions = [getattr(cls, k) == v for k, v in filters.items() if hasattr(cls, k)]
        if conditions:
            return query.where(*filters)

        return query
