

from future import utils


if utils.PY2:
    from io import open
    from future_builtins import ascii, oct, hex
    from __builtin__ import unichr as chr, pow as _builtin_pow
    import __builtin__

    # Only for backward compatibility with future v0.8.2:
    isinstance = __builtin__.isinstance

    # Warning: Python 2's input() is unsafe and MUST not be able to be used
    # accidentally by someone who expects Python 3 semantics but forgets
    # to import it on Python 2. Versions of ``future`` prior to 0.11
    # deleted it from __builtin__.  Now we keep in __builtin__ but shadow
    # the name like all others. Just be sure to import ``input``.

    input = raw_input

    from future.builtins.newnext import newnext as next
    from future.builtins.newround import newround as round
    from future.builtins.newsuper import newsuper as super

    _SENTINEL = object()

    def pow(x, y, z=_SENTINEL):
        
        try:
            if z == _SENTINEL:
                return _builtin_pow(x, y)
            else:
                return _builtin_pow(x, y, z)
        except ValueError:
            if z == _SENTINEL:
                return _builtin_pow(x+0j, y)
            else:
                return _builtin_pow(x+0j, y, z)

    # ``future`` doesn't support Py3.0/3.1. If we ever did, we'd add this:
    #     callable = __builtin__.callable

    __all__ = ['ascii', 'chr', 'hex', 'input', 'isinstance', 'next', 'oct',
               'open', 'pow', 'round', 'super']

else:
    import builtins
    ascii = builtins.ascii
    chr = builtins.chr
    hex = builtins.hex
    input = builtins.input
    next = builtins.next
    # Only for backward compatibility with future v0.8.2:
    isinstance = builtins.isinstance
    oct = builtins.oct
    open = builtins.open
    pow = builtins.pow
    round = builtins.round
    super = builtins.super

    __all__ = []

    # The callable() function was removed from Py3.0 and 3.1 and
    # reintroduced into Py3.2+. ``future`` doesn't support Py3.0/3.1. If we ever
    # did, we'd add this:
    # try:
    #     callable = builtins.callable
    # except AttributeError:
    #     # Definition from Pandas
    #     def callable(obj):
    #         return any("__call__" in klass.__dict__ for klass in type(obj).__mro__)
    #     __all__.append('callable')
