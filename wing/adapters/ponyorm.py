from wing import fields
from ..errors import IntegrityError


class Adapter(object):
    def __init__(self, cls):
        self.cls = cls

    pass