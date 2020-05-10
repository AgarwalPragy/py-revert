__all__ = ['DBError', 'NoTransactionActiveError', 'InTransactionError', 'AmbiguousRedoError']


class DBError(Exception):
    pass


class NoTransactionActiveError(DBError):
    pass


class InTransactionError(DBError):
    pass


class AmbiguousRedoError(DBError):
    pass
