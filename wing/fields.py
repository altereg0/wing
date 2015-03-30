from datetime import datetime
import peewee


def create_resource_field(orm_field):
    """
    Create resource field based on ORM field type
    :param orm_field: ORM field
    """
    mapping = {
        peewee.PrimaryKeyField: IntegerField,
        peewee.CharField: CharField,
        peewee.TextField: TextField,
        peewee.IntegerField: IntegerField,
        peewee.BooleanField: BooleanField,
        peewee.DateTimeField: DateTimeField,
        peewee.DateField: DateField,
    }

    if isinstance(orm_field, peewee.Field):
        is_required = not orm_field.null and orm_field.default is None
        is_nullable = orm_field.null

        if isinstance(orm_field, peewee.ForeignKeyField):
            rel_cls = orm_field.rel_model
            rel_pk = rel_cls._meta.primary_key.name

            return ForeignKeyField(orm_field.name, rel_cls, rel_pk, required=is_required, null=is_nullable)

        cls = mapping.get(type(orm_field))

        if not cls:
            raise Exception('Unsupported field type %s' % type(orm_field))

        return cls(orm_field.name, is_required, null=is_nullable)


class Field(object):
    """
    Hydrator field

    Implement hydrate and dehydrate methods
    """

    def __init__(self, attribute, required=False, null=False, readonly=False):
        self.attribute = attribute
        self.readonly = readonly
        self.required = required
        self.null = null

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
        return int(value)


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

        return datetime.strptime(value, self.format)


class DateField(DateTimeField):
    def __init__(self, *args, format="%Y-%m-%d", **kwargs):
        super(DateField, self).__init__(*args, format=format, **kwargs)

    def convert(self, value):
        if value is None:
            return None

        return super(DateField, self).date()


class ForeignKeyField(Field):
    def __init__(self, attribute, rel_cls, rel_pk='id', rel_pk_coerce=int, *args, **kwargs):
        super(ForeignKeyField, self).__init__(attribute, *args, **kwargs)

        self.rel_cls = rel_cls
        self.rel_pk = rel_pk
        self.rel_pk_field = getattr(self.rel_cls, self.rel_pk)
        self.rel_pk_coerce = rel_pk_coerce

    def dehydrate(self, obj):
        """dehydrate field from object"""
        rel_obj = getattr(obj, self.attribute)
        return getattr(rel_obj, self.rel_pk)

    def convert(self, value):
        rel_pk_field = getattr(self.rel_cls, self.rel_pk)
        return self.rel_cls.get(rel_pk_field == self.rel_pk_coerce(value))


class ToManyField(Field):
    def __init__(self, attribute, rel_resource, *args, **kwargs):
        super(ToManyField, self).__init__(attribute, *args, **kwargs)

        self.rel_resource = rel_resource
        self.rel_pk = rel_resource._meta.primary_key

    def dehydrate(self, obj):
        qs = getattr(obj, self.attribute)[:1000]

        return [getattr(rel_obj, self.rel_pk) for rel_obj in qs]

    def hydrate(self, obj, value):
        raise NotImplemented