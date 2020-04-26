class DBError(Exception):
    pass


class UnsavableObjectError(DBError):
    pass


class ClassAlreadyRegisteredError(DBError):
    pass


class NoSuchClassRegisteredError(DBError):
    pass


class NoTransactionActiveError(DBError):
    pass