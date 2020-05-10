from revert.exceptions import DBError

__all__ = ['ORMError', 'UnsavableObjectError', 'ClassAlreadyRegisteredError', 'NoSuchClassRegisteredError']


class ORMError(DBError):
    pass


class UnsavableObjectError(ORMError):
    pass


class ClassAlreadyRegisteredError(ORMError):
    pass


class NoSuchClassRegisteredError(ORMError):
    pass
