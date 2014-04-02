from som.primitives.primitives import Primitives
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.array import Array
from som.vmobjects.primitive   import Primitive 


def _holder(ivkbl, rcvr, args, domain):
    return rcvr.get_holder()


def _signature(ivkbl, rcvr, args, domain):
    return rcvr.get_signature()


def _invoke_on_with(ivkbl, rcvr, args, domain):
    assert isinstance(rcvr,    Primitive)
    assert isinstance(args[0], AbstractObject)
    assert isinstance(args[1], Array) or args[1] is None
    return rcvr.invoke_unenforced(args[0], args[1], domain)


class PrimitivePrimitives(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(Primitive("holder",
                                                   self._universe, _holder))
        self._install_instance_primitive(Primitive("signature",
                                                   self._universe, _signature))
        self._install_instance_primitive(Primitive("invokeOn:with:",
                                                   self._universe, _invoke_on_with))
