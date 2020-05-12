from revert.exceptions import DBError

__all__ = ['OGMError', 'UnsavableObjectError', 'ClassAlreadyRegisteredError', 'NoSuchClassRegisteredError']


class OGMError(DBError):
    pass


class UnsavableObjectError(OGMError):
    pass


class ClassAlreadyRegisteredError(OGMError):
    pass


class NoSuchClassRegisteredError(OGMError):
    pass
