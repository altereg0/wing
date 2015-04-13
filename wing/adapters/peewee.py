import peewee
from wing.fields import *
from ..errors import IntegrityError


class Adapter(object):
    def __init__(self, cls):
        self.cls = cls

    def select(self, filters=None):
        query = self.cls.select()
        if filters:
            query = self.apply_filters(query, filters)

        return query

    def delete(self, filters=None):
        """
        Delete objects matching filters parameter
        :return count of deleted rows
        """
        query = self.cls.delete()

        if filters:
            query = self.apply_filters(query, filters)

        return query.execute()

    def create_object(self):
        return self.cls()

    def save_object(self, obj):
        try:
            obj.save()
        except peewee.IntegrityError as e:
            raise IntegrityError(e.args)

    def get_fields(self, excludes=None):
        fields = {}
        if not excludes:
            excludes = []

        for key, field in self.cls._meta.fields.items():
            if key not in excludes:
                field = create_resource_field(field)
                if field is not None:
                    fields[key] = field

        return fields

    def apply_filters(self, query, filters):
        conditions = [_filter_get_expr(getattr(self.cls, field), type, val) for field, type, val in filters if
                      hasattr(self.cls, field)]

        if conditions:
            return query.where(*conditions)

        return query


def _filter_get_expr(field, filter_type, value):
    if filter_type == 'exact':
        return field == value
    elif filter_type == 'gt':
        return field > value
    elif filter_type == 'gte':
        return field >= value
    elif filter_type == 'lt':
        return field < value
    elif filter_type == 'lte':
        return field <= value
    elif filter_type == 'contains':
        return field.contains(value)
    elif filter_type == 'startswith':
        return field.startswith(value)
    elif filter_type == 'endswith':
        return field.endswith(value)
    elif filter_type == 'is_null':
        return field.is_null(value)
    elif filter_type == 'in':
        if not isinstance(value, list):
            value = value.split(',')

        return field.in_(value)
    else:
        raise NotImplemented


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
        if isinstance(orm_field, peewee.PrimaryKeyField):
            is_required = False

        is_nullable = orm_field.null

        if isinstance(orm_field, peewee.ForeignKeyField):
            return

        cls = mapping.get(type(orm_field))

        if not cls:
            raise Exception('Unsupported field type %s' % type(orm_field))

        return cls(orm_field.name, is_required, null=is_nullable)