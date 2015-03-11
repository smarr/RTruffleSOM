import unittest
from som.vmobjects.array import Array
from som.vmobjects.integer import Integer


class ArrayTest(unittest.TestCase):

    def test_empty_array(self):
        arr = Array.from_size(0)
        self.assertEqual(arr.get_number_of_indexable_fields(), 0)

    def test_copy_and_extend_partially_empty(self):
        arr = Array.from_size(3)

        int_obj = Integer(42)
        arr.set_indexable_field(0, int_obj)
        new_arr = arr.copy_and_extend_with(int_obj)

        self.assertIsNot(arr, new_arr)
        self.assertEqual(4, new_arr.get_number_of_indexable_fields())
