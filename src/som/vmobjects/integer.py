from som.vmobjects.abstract_object import AbstractObject


class Integer(AbstractObject):
    
    _immutable_fields_ = ["_embedded_integer"]
    
    def __init__(self, value):
        AbstractObject.__init__(self)
        self._embedded_integer = value
    
    def get_embedded_integer(self):
        return self._embedded_integer
        
    def get_embedded_value(self):
        """This Method is polymorphic with BigInteger"""
        return self._embedded_integer
    
    def __str__(self):
        return str(self._embedded_integer)
    
    def get_class(self, universe):
        return universe.integerClass

    def get_domain(self, universe):
        return universe.standardDomain

    def set_domain(self, domain):
        pass

    def has_domain(self):
        """ Integer is a primitive type. Its objects are immutable and not owned
            by any particular domain. """
        return False


def integer_value_fits(value):
    return value <= 2147483647 and value > -2147483646
