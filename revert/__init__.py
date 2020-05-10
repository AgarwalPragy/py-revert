# noinspection PyUnresolvedReferences
from . import config
# noinspection PyUnresolvedReferences
from .exceptions import *
from .revert import *

__all__ = revert.__all__ + exceptions.__all__ + ['orm', '__author__', '__email__', '__version__', 'config']

__author__ = """Pragy Agarwal"""
__email__ = 'agar.pragy@gmail.com'
__version__ = '0.1.0'

# noinspection PyUnresolvedReferences
from . import orm

# todo: remodel revert as a vcs+db
# todo: add content hash based verification and security
# todo: add sync with dropbox, google drive, github, and support for custom syncs
