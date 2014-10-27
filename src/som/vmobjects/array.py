from rpython.rlib.objectmodel import instantiate
from .abstract_object import AbstractObject
from som.vm.globals import nilObject


class Array(AbstractObject):

    @staticmethod
    def from_size(size):
        self = instantiate(Array)
        self._indexable_fields = [nilObject] * size
        return self

    @staticmethod
    def from_values(values):
        self = instantiate(Array)
        self._indexable_fields = values
        return self

    @staticmethod
    def from_objects(values):
        return Array.from_values(values)

    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        assert 0 <= index < len(self._indexable_fields)
        return self._indexable_fields[index]

    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        assert 0 <= index < len(self._indexable_fields)
        self._indexable_fields[index] = value

    def as_argument_array(self):
        return self._indexable_fields

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return len(self._indexable_fields)

    def copy(self):
        return Array.from_values(self._indexable_fields[:])

    def copy_and_extend_with(self, value):
        old_size = len(self._indexable_fields)
        new_size = old_size + 1

        new = [None] * new_size
        for i, val in enumerate(self._indexable_fields):
            new[i] = val
        new[old_size] = value

        return Array.from_values(new)

    def get_class(self, universe):
        return universe.arrayClass
