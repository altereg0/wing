class DoesNotExist(Exception):
    pass


class NoAdapter(Exception):
    pass


class FieldValidationError(Exception):
    def __init__(self, field, message):
        self.field = field
        super().__init__(message)

    def __str__(self):
        return '{}: {}'.format(self.field, *self.args)


class MissingRequiredFieldError(FieldValidationError):
    def __init__(self, field, message=None):
        super().__init__(field, message or 'Field is required')


class NotNullFieldError(FieldValidationError):
    def __init__(self, field, message=None):
        super().__init__(field, message or 'Not null field constraint failed')
