from ..errors import NoAdapter


def detect_adapter(cls):
    try:
        import peewee

        if issubclass(cls, peewee.Model):
            from .peewee import Adapter
            return Adapter
    except ImportError:
        pass

    raise NoAdapter('No adapter found for class "{0}"'.format(cls.__name__))
