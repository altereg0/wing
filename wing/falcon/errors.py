import falcon
from falcon import NoRepresentation, HTTPError


class HTTPNotModified(NoRepresentation, HTTPError):
    """
    304 Not Modified
    """

    def __init__(self, **kwargs):
        super(HTTPNotModified, self).__init__(falcon.HTTP_304, **kwargs)
