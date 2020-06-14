__all__ = ['DBError', 'NoTransactionActiveError', 'InTransactionError', 'AmbiguousRedoError', 'AmbiguousUndoError']


class DBError(Exception):
    pass


class NoTransactionActiveError(DBError):
    pass


class InTransactionError(DBError):
    pass


class AmbiguousRedoError(DBError):
    pass


class AmbiguousUndoError(DBError):
    pass
