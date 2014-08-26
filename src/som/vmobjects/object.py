from rpython.rlib.jit import promote, elidable_promote
from som.vmobjects.abstract_object import AbstractObject


class Object(AbstractObject):

    ## TODO: see whether it is a really good idea to make _domain quasi immutable
    ##       in situations with actors, for instance, were we change the owner
    ##       domain of an object frequently, that might not have the desired
    ##       effect
    _immutable_fields_ = ["_class", "_fields", "_domain?"]
    
    # Static field indices and number of object fields
    NUMBER_OF_OBJECT_FIELDS = 0

    NUMBER_OF_DIRECT_FIELDS = 5

    def __init__(self, nilObject, domain, obj_class, number_of_fields = -1):
        nilObject = promote(nilObject)
        num_fields = (number_of_fields if number_of_fields != -1
                      else self.NUMBER_OF_OBJECT_FIELDS)
        
        self._field1 = nilObject
        self._field2 = nilObject
        self._field3 = nilObject
        self._field4 = nilObject
        self._field5 = nilObject
        
        if num_fields > self.NUMBER_OF_DIRECT_FIELDS:
            self._fields = [nilObject] * (num_fields - self.NUMBER_OF_DIRECT_FIELDS)
        else:
            self._fields = []
             
        self._class = obj_class or nilObject

        self._domain = domain  ## TODO: should we make sure this is never None???

    def get_class(self, universe):
        return self._class

    def set_class(self, value):
        self._class = value

    def get_field_name(self, index):
        # Get the name of the field with the given index
        return self._class.get_instance_field_name(index)

    def get_field_index(self, name):
        # Get the index for the field with the given name
        return self._class.lookup_field_index(name)

    def get_number_of_fields(self):
        # Get the number of fields in this object
        return len(self._fields)

    def get_field(self, index):
        # Get the field with the given index
        assert isinstance(index, int)
        
        if index == 0: return self._field1
        if index == 1: return self._field2
        if index == 2: return self._field3
        if index == 3: return self._field4
        if index == 4: return self._field5
        return self._fields[index - self.NUMBER_OF_DIRECT_FIELDS]
  
    def set_field(self, index, value):
        # Set the field with the given index to the given value
        assert isinstance(index, int)
        assert isinstance(value, AbstractObject)
        
        if index == 0: self._field1 = value; return
        if index == 1: self._field2 = value; return
        if index == 2: self._field3 = value; return
        if index == 3: self._field4 = value; return
        if index == 4: self._field5 = value; return
        self._fields[index - self.NUMBER_OF_DIRECT_FIELDS] = value

    def get_domain(self, universe):
        return promote(self._domain)

    def set_domain(self, domain):
        self._domain = domain

    def has_domain(self):
        return True
