from datetime import datetime
from urllib.parse import urlparse
from .errors import DoesNotExist, InvalidValue


class Field(object):
    """
    Resource field
    """

    def __init__(self, attribute, required=False, null=False, readonly=False, show=None, pk=False):
        if show is None:
            show = ['details', 'list']

        self.attribute = attribute
        self.readonly = readonly
        self.required = required
        self.null = null
        self.show = show

    def hydrate(self, obj, value):
        """hydrate field to object"""
        if self.readonly:
            return

        value = self.convert(value)

        setattr(obj, self.attribute, value)

    def dehydrate(self, obj):
        """dehydrate field from object"""
        return getattr(obj, self.attribute)

    def convert(self, value):
        return value


class CharField(Field):
    pass


class TextField(Field):
    pass


class IntegerField(Field):
    def convert(self, value):
        try:
            return int(value)
        except ValueError as e:
            raise InvalidValue(*e.args)


class BooleanField(Field):
    def convert(self, value):
        return bool(value)


class DateTimeField(Field):
    def __init__(self, *args, format="%Y-%m-%d %H:%M:%S", **kwargs):
        super(DateTimeField, self).__init__(*args, **kwargs)
        self.format = format

    def convert(self, value):
        if value is None:
            return None
        try:
            return datetime.strptime(value, self.format)
        except ValueError:
            raise InvalidValue('Invalid datetime format')


class DateField(DateTimeField):
    def __init__(self, *args, format="%Y-%m-%d", **kwargs):
        super(DateField, self).__init__(*args, format=format, **kwargs)

    def convert(self, value):
        if value is None:
            return None
        try:
            return super(DateField, self).date()
        except:
            raise InvalidValue('Invalid date format')


class URLField(CharField):
    def convert(self, value):
        if value is None:
            return None

        parts = urlparse(value, 'http')

        if not parts.netloc:
            raise InvalidValue('Invalid URL value')

        return parts.geturl()


class ForeignKeyField(Field):
    def __init__(self, attribute, rel_resource, *args, **kwargs):
        super(ForeignKeyField, self).__init__(attribute, *args, **kwargs)

        self.rel_resource = rel_resource

    def dehydrate(self, obj):
        """dehydrate field from object"""
        rel_obj = getattr(obj, self.attribute)

        # return getattr(rel_obj, self.rel_resource._meta.primary_key) if rel_obj is not None else None
        return getattr(rel_obj, self.rel_resource._meta.pk) if rel_obj is not None else None

    def convert(self, value):
        # rel_pk = self.rel_resource._meta.primary_key
        rel_pk = self.rel_resource._meta.pk
        rel_field = self.rel_resource.fields[rel_pk]

        filters = self.rel_resource._filters_from_kwargs(**{rel_pk: rel_field.convert(value)})
        qs = self.rel_resource.db.select(filters)[:1]

        if len(qs) == 0:
            raise DoesNotExist()

        return qs[0]


class ToManyField(Field):
    def __init__(self, attribute, rel_resource, full=False, *args, **kwargs):
        super(ToManyField, self).__init__(attribute, *args, **kwargs)

        self.rel_resource = rel_resource
        self.rel_pk = rel_resource._meta.primary_key
        self.full = full

    def dehydrate(self, obj):
        qs = getattr(obj, self.attribute)[:1000]

        return [self.dehydrate_rel_obj(rel_obj) for rel_obj in qs]

    def dehydrate_rel_obj(self, rel_obj):
        if self.full:
            return self.rel_resource.dehydrate(rel_obj, None)
        else:
            return getattr(rel_obj, self.rel_pk)

    def hydrate(self, obj, value):
        raise NotImplemented