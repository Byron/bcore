

from __future__ import division, absolute_import, print_function

import itertools
from future import utils

if not utils.PY3:
    filter = itertools.ifilter
    map = itertools.imap
    from future.types import newrange as range
    zip = itertools.izip
    __all__ = ['filter', 'map', 'range', 'zip']
else:
    import builtins
    filter = builtins.filter
    map = builtins.map
    range = builtins.range
    zip = builtins.zip
    __all__ = []

