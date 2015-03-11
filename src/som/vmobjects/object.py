from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object_without_fields import ObjectWithoutFields
from som.vm.globals import nilObject

_EMPTY_LIST = []


class Object(ObjectWithoutFields):

    _immutable_fields_ = ["_object_fields"]
    
    # Static field indices and number of object fields
    NUMBER_OF_OBJECT_FIELDS = 0

    def __init__(self, obj_class, number_of_fields = NUMBER_OF_OBJECT_FIELDS):
        cls = obj_class if obj_class is not None else nilObject
        ObjectWithoutFields.__init__(self, cls)

        if obj_class is not None:
            self._object_fields = [nilObject] * obj_class.get_number_of_instance_fields()
        else:
            self._object_fields = [nilObject] * number_of_fields

    def get_field_name(self, index):
        # Get the name of the field with the given index
        return self._class.get_instance_field_name(index)

    def get_field_index(self, name):
        # Get the index for the field with the given name
        return self._class.lookup_field_index(name)

    def get_number_of_fields(self):
        # Get the number of fields in this object
        return len(self._object_fields)

    def get_field(self, field_idx):
        # Get the field with the given index
        assert isinstance(field_idx, int)
        assert 0 <= field_idx < len(self._object_fields)

        return self._object_fields[field_idx]
  
    def set_field(self, field_idx, value):
        # Set the field with the given index to the given value
        assert isinstance(field_idx, int)
        assert 0 <= field_idx < len(self._object_fields)
        assert isinstance(value, AbstractObject)

        self._object_fields[field_idx] = value
