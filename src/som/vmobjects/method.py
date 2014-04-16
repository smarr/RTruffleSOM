from __future__ import absolute_import

from rpython.rlib import jit

from som.interpreter.control_flow import ReturnException

from som.vmobjects.abstract_object import AbstractObject


class Method(AbstractObject):
    
    _immutable_fields_ = ["_signature", "_invokable",
                          "_embedded_block_methods", "_universe", "_holder"]

    def __init__(self, signature, invokable, embedded_block_methods, universe):
        AbstractObject.__init__(self)

        self._signature    = signature
        self._invokable    = invokable

        self._embedded_block_methods = embedded_block_methods
        self._universe = universe

        self._holder   = None

    @jit.elidable_promote('all')
    def get_universe(self):
        return self._universe

    @jit.elidable_promote('all')
    def is_primitive(self):
        return False

    @jit.elidable_promote('all')
    def is_invokable(self):
        """ We use this method to identify methods and primitives """
        return True
  
    @jit.elidable_promote('all')
    def get_signature(self):
        return self._signature

    @jit.elidable_promote('all')
    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value
        for method in self._embedded_block_methods:
            method.set_holder(value)

    @jit.elidable_promote('all')
    def get_number_of_arguments(self):
        return self.get_signature().get_number_of_signature_arguments()

    def invoke_enforced(self, receiver, args, executing_domain):
        return self._invokable.invoke_enforced(receiver, args, executing_domain)

    def invoke_enforced_void(self, receiver, args, executing_domain):
        self._invokable.invoke_enforced_void(receiver, args, executing_domain)

    def invoke_unenforced(self, receiver, args, executing_domain):
        return self._invokable.invoke_unenforced(receiver, args, executing_domain)

    def invoke_unenforced_void(self, receiver, args, executing_domain):
        self._invokable.invoke_unenforced_void(receiver, args, executing_domain)

    def __str__(self):
        return ("Method(" + self.get_holder().get_name().get_string() + ">>" +
                str(self.get_signature()) + ")")
    
    def get_class(self, universe):
        return universe.methodClass

    def merge_point_string(self):
        """ debug info for the jit """
        return "%s>>%s" % (self.get_holder().get_name().get_string(),
                           self.get_signature().get_string())

    def get_domain(self, universe):
        return universe.standardDomain

    def set_domain(self, domain):
        pass

    def has_domain(self):
        """ Method is a primitive type. Its objects are immutable and not owned
            by any particular domain. """
        return False
