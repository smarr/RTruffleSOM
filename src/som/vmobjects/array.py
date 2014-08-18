from rpython.rlib.jit import promote
from .abstract_object import AbstractObject


class Array(AbstractObject):

    _immutable_fields_ = ["_indexable_fields", "_domain?"]
    
    def __init__(self, nilObject, number_of_indexable_fields, domain, values = None):
        AbstractObject.__init__(self)
        nilObject = promote(nilObject)

        # Private array of indexable fields
        if values is None:
            self._indexable_fields = [nilObject] * promote(number_of_indexable_fields)
        else:
            self._indexable_fields = values
        self._domain = domain
        
    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        return self._indexable_fields[index]
  
    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        self._indexable_fields[index] = value

    def get_indexable_fields(self):
        return self._indexable_fields

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return len(self._indexable_fields)

    def copy_and_extend_with(self, value, universe):
        ## TODO: the new owner domain here should be determined by the current
        ##       domain executing the method..., needs to be passed in
        result = Array(universe.nilObject,
                       self.get_number_of_indexable_fields() + 1, self._domain)

        self._copy_indexable_fields_to(result)

        # Insert the given object as the last indexable field in the new array
        result.set_indexable_field(self.get_number_of_indexable_fields(), value)
        return result

    def _copy_indexable_fields_to(self, destination):
        for i, value in enumerate(self._indexable_fields):
            destination._indexable_fields[i] = value

    def get_class(self, universe):
        return universe.arrayClass

    def get_domain(self, universe):
        return self._domain

    def set_domain(self, domain):
        self._domain = domain
