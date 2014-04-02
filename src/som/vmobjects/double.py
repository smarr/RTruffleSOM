from som.vmobjects.abstract_object import AbstractObject


class Double(AbstractObject):

    _immutable_fields_ = ["_embedded_double"]
    
    def __init__(self, value):
        AbstractObject.__init__(self)
        self._embedded_double = value
    
    def get_embedded_double(self):
        return self._embedded_double

    def get_class(self, universe):
        return universe.doubleClass

    def get_domain(self, universe):
        return universe.standardDomain

    def set_domain(self, domain):
        pass

    def has_domain(self):
        """ Double is a primitive type. Its objects are immutable and not owned
            by any particular domain. """
        return False
