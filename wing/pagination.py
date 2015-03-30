class Paginator(object):
    page_number = 1

    def __init__(self, query, page_size):
        self.query = query
        self.page_size = page_size

    @property
    def total_count(self):
        """
        Total items count
        """
        return self.query.count()

    @property
    def offset(self):
        """
        Current page offset
        """
        return self.page_size * (self.page_number - 1)

    @property
    def items(self):
        """
        Page items
        """
        return self.query[self.offset:self.offset + self.page_size]
