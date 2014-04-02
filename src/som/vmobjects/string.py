from som.vmobjects.abstract_object import AbstractObject

class String(AbstractObject):
    _immutable_fields_ = ["_string"]
    
    def __init__(self, value):
        AbstractObject.__init__(self)
        self._string = value
    
    def get_embedded_string(self):
        return self._string
        
    def __str__(self):
        return "\"" + self._string + "\""

    def get_class(self, universe):
        return universe.stringClass

    def get_domain(self, universe):
        return universe.standardDomain

    def set_domain(self, domain):
        pass

    def has_domain(self):
        """ String is a primitive type. Its objects are immutable and not owned
            by any particular domain. """
        return False
