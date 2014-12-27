from rpython.rlib.debug import make_sure_not_resized
from rpython.rlib.jit import promote
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.integer import Integer


_EMPTY_LIST = []

class IntegerArray(AbstractObject):

    _immutable_fields_ = ['_int_array']

    def __init__(self, size, values = None):
        AbstractObject.__init__(self)

        if values is None:
            if size > 0:
                self._int_array = [0] * promote(size)
            else:
                self._int_array = _EMPTY_LIST
        else:
            self._int_array = values
        make_sure_not_resized(self._int_array)

    def get_idx(self, idx):
        return Integer(self._int_array[idx])

    def set_idx(self, idx, obj):
        assert isinstance(obj, Integer)
        self._int_array[idx] = obj.get_embedded_integer()

    def get_size(self):
        return len(self._int_array)

    def get_int_array(self):
        return self._int_array

    def copy(self):
        return IntegerArray(0, self._int_array[:])

    def copy_and_extend_with(self, value, universe):
        assert isinstance(value, Integer)
        result = IntegerArray(len(self._int_array) + 1)
        self._copy_to(result)
        result.set_idx(len(self._int_array), value)
        return result

    def _copy_to(self, destination):
        for i, value in enumerate(self._int_array):
            destination._int_array[i] = value

    def get_class(self, universe):
        return universe.integerArrayClass
