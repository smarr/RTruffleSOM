from rpython.rlib import jit
from som.vmobjects.block import Block
from som.vmobjects.method import Method
from som.vmobjects.primitive   import Primitive
from som.primitives.primitives import Primitives


def _at(ivkbl, rcvr, args):
    i    = args[0]
    return  rcvr.get_indexable_field(i.get_embedded_integer() - 1)


def _atPut(ivkbl, rcvr, args):
    value = args[1]
    index = args[0]

    rcvr.set_indexable_field(index.get_embedded_integer() - 1, value)
    return value


def _length(ivkbl, rcvr, args):
    return ivkbl.get_universe().new_integer(
        rcvr.get_number_of_indexable_fields())


def _new(ivkbl, rcvr, args):
    length = args[0]

    return ivkbl.get_universe().new_array_with_length(
        length.get_embedded_integer())


def _copy(ivkbl, rcvr, args):
    return rcvr.copy()


def _putAll(ivkbl, rcvr, args):
    arg = args[0]
    if isinstance(arg, Block):
        rcvr.set_all_with_block(arg)
        return rcvr

    ## It is a simple value, just put it into the array

    ## TODO: move to array, and adapt to use strategies
    rcvr.set_all(arg)
    return rcvr


class ArrayPrimitives(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(Primitive("at:",     self._universe, _at))
        self._install_instance_primitive(Primitive("at:put:", self._universe, _atPut))
        self._install_instance_primitive(Primitive("length",  self._universe, _length))
        self._install_instance_primitive(Primitive("copy",    self._universe, _copy))
        self._install_instance_primitive(Primitive("putAll:", self._universe, _putAll))

        self._install_class_primitive(Primitive("new:",       self._universe, _new))
