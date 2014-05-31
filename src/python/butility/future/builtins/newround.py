
 
from future.utils import PYPY, PY26, bind_method

# Use the decimal module for simplicity of implementation (and
# hopefully correctness).
from decimal import Decimal, ROUND_HALF_EVEN


def newround(number, ndigits=None):
    
    return_int = False
    if ndigits is None:
        return_int = True
        ndigits = 0
    if hasattr(number, '__round__'):
        return number.__round__(ndigits)
    
    if ndigits < 0:
        raise NotImplementedError('negative ndigits not supported yet')
    exponent = Decimal('10') ** (-ndigits)

    if PYPY:
        # Work around issue #24: round() breaks on PyPy with NumPy's types
        if 'numpy' in repr(type(number)):
            number = float(number)

    if not PY26:
        d = Decimal.from_float(number).quantize(exponent,
                                            rounding=ROUND_HALF_EVEN)
    else:
        d = from_float_26(number).quantize(exponent, rounding=ROUND_HALF_EVEN)

    if return_int:
        return int(d)
    else:
        return float(d)
 

### From Python 2.7's decimal.py. Only needed to support Py2.6:

def from_float_26(f):
    
    import math as _math
    from decimal import _dec_from_triple    # only available on Py2.6 and Py2.7 (not 3.3)

    if isinstance(f, (int, long)):        # handle integer inputs
        return Decimal(f)
    if _math.isinf(f) or _math.isnan(f):  # raises TypeError if not a float
        return Decimal(repr(f))
    if _math.copysign(1.0, f) == 1.0:
        sign = 0
    else:
        sign = 1
    n, d = abs(f).as_integer_ratio()
    # int.bit_length() method doesn't exist on Py2.6:
    def bit_length(d):
        if d != 0:
            return len(bin(abs(d))) - 2
        else:
            return 0
    k = bit_length(d) - 1
    result = _dec_from_triple(sign, str(n*5**k), -k)
    return result


__all__ = ['newround']
