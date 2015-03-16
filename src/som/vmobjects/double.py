from rpython.rlib.rfloat import formatd, DTSF_ADD_DOT_0, DTSF_STR_PRECISION
from som.vm.globals import trueObject
from som.vm.globals import falseObject

from som.vmobjects.abstract_object import AbstractObject

import math


class Double(AbstractObject):

    _immutable_fields_ = ["_embedded_double"]
    
    def __init__(self, value):
        AbstractObject.__init__(self)
        assert isinstance(value, float)
        self._embedded_double = value
    
    def get_embedded_double(self):
        return self._embedded_double

    def get_class(self, universe):
        return universe.doubleClass

    @staticmethod
    def _get_float(obj):
        from .integer import Integer
        if isinstance(obj, Double):
            return obj.get_embedded_double()
        if isinstance(obj, Integer):
            return float(obj.get_embedded_integer())
        raise ValueError("Cannot coerce %s to Double!" % obj)

    def prim_multiply(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(self._embedded_double * r)

    def prim_add(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(self._embedded_double + r)

    def prim_bit_xor(self, right, universe):
        raise NotImplementedError("bit operations on Double are not supported.")

    def prim_as_string(self, universe):
        s = formatd(self._embedded_double, "g", DTSF_STR_PRECISION, DTSF_ADD_DOT_0)
        return universe.new_string(s)

    def prim_subtract(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(self._embedded_double - r)

    def prim_double_div(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(self._embedded_double / r)

    def prim_int_div(self, right, universe):
        r = self._get_float(right)
        return universe.new_integer(int(self._embedded_double / r))

    def prim_modulo(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(math.fmod(self._embedded_double, r))

    def prim_remainder(self, right, universe):
        r = self._get_float(right)
        return universe.new_double(math.fmod(self._embedded_double, r))

    def prim_and(self, right, universe):
        raise NotImplementedError("bit operations on Double are not supported.")

    def prim_equals(self, right, universe):
        r = self._get_float(right)
        if self._embedded_double == r:
            return trueObject
        else:
            return falseObject

    def prim_less_than(self, right, universe):
        r = self._get_float(right)
        if self._embedded_double < r:
            return trueObject
        else:
            return falseObject
