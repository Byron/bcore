from bcore.component import *
import bcore

class I1(bcore.InterfaceBase):
    def foo(self):
        print "foo"

class I2(bcore.InterfaceBase):
    def phoo(self):
        print "blah!"

class I3(I1):
    def bar(self):
        print "overloaded foo"

class I4(I2, dict):
    def func1(self):
        print "function!"
