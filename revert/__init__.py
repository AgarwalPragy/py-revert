# noinspection PyUnresolvedReferences
from . import config
# noinspection PyUnresolvedReferences
from .exceptions import *
from .revert import *

__author__ = """Pragy Agarwal"""
__email__ = 'agar.pragy@gmail.com'
__version__ = '0.2.0'

# noinspection PyUnresolvedReferences
from . import ogm

# todo: remodel revert as a vcs+db
# todo: add content hash based verification and security
# todo: add sync with dropbox, google drive, github, and support for custom syncs
