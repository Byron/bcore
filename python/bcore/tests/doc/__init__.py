#-*-coding:utf-8-*-
"""
@package bcore.tests.doc
A special package which contains tests that are used to be extracted as doxygen
snippets.

Its useful if you want to include example code within your documentation. If you
would include it clear-text, you risk the code is not actually working, or that
the code will stop working at some point without being noticed. This could cause
the documentation not be correct, which is even worse than no documentation.

The solution is to put your example code into a file of your choice within this
package and refer to it using the [\@snippet doxygen
command](http://www.stack.nl/~dimitri/doxygen/commands.html#cmdsnippet).

In your file you define your code example within a test-case to assure it will
be run.

@code
## [snippet for myfeature]
myfeature()
## [snippet for myfeature]
@endcode

In your documentation docstring, you add the snippet like so:
@code
def myfeature():
    "@snippet bcore/tests/doc/test_examples.py snippet for myfeature"
    pass
@endcode
@copyright 2012 Sebastian Thiel
"""
__all__ = []

