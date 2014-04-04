from som.vmobjects.abstract_object    import AbstractObject
from som.vmobjects.domain import request_primitive_execution


class Primitive(AbstractObject):
    _immutable_fields_ = ["_prim_fun", "_is_empty", "_signature",
                          "_holder", "_universe"]
        
    def __init__(self, signature_string, universe, prim_fun,
                 is_empty = False, is_unenforced = False):
        AbstractObject.__init__(self)
        
        self._signature = universe.symbol_for(signature_string)

        self._prim_fun  = prim_fun
        self._is_empty  = is_empty
        self._holder    = None
        self._universe  = universe
        self._is_unenforced = is_unenforced

    def get_universe(self):
        return self._universe

    def invoke_enforced(self, rcvr, args, executing_domain):
        if self._is_unenforced:
            return self.invoke_unenforced(rcvr, args, executing_domain)
        else:
            return request_primitive_execution(self, rcvr, args, executing_domain)

    def invoke_enforced_void(self, rcvr, args, executing_domain):
        self.invoke_enforced(rcvr, args, executing_domain)

    def invoke_unenforced(self, rcvr, args, executing_domain):
        inv = self._prim_fun
        return inv(self, rcvr, args, executing_domain)

    def invoke_unenforced_void(self, rcvr, args, executing_domain):
        self.invoke_unenforced(rcvr, args, executing_domain)

    def is_primitive(self):
        return True
    
    def is_invokable(self):
        """In the RPython version, we use this method to identify methods 
           and primitives
        """
        return True

    def get_signature(self):
        return self._signature

    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value

    def is_empty(self):
        # By default a primitive is not empty
        return self._is_empty
    
    def get_class(self, universe):
        return universe.primitiveClass

    def get_domain(self, universe):
        return universe.standardDomain

    def set_domain(self, domain):
        pass

    def is_unenforced(self):
        return self._is_unenforced

    def set_unenforced(self):
        self._is_unenforced = True

    def has_domain(self):
        """ Primitive is a primitive type. Its objects are immutable and not owned
            by any particular domain. """
        return False

    def __str__(self):
        return ("Primitive(" + self.get_holder().get_name().get_string() + ">>"
                + str(self.get_signature()) + ")")


def empty_primitive(signature_string, universe, is_unenforced):
    """ Return an empty primitive with the given signature """
    return Primitive(signature_string, universe, _invoke, True, is_unenforced)


def _invoke(ivkbl, rcvr, args, domain):
    """ Write a warning to the screen """
    print "Warning: undefined primitive %s called" % ivkbl.get_signature()
