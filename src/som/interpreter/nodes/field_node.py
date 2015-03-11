from .expression_node import ExpressionNode

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object          import Object


class _AbstractFieldNode(ExpressionNode):

    _immutable_fields_ = ["_self_exp?", "_field_idx"]
    _child_nodes_      = ["_self_exp"]

    def __init__(self, self_exp, field_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        self._self_exp  = self.adopt_child(self_exp)
        self._field_idx = field_idx


class FieldReadNode(_AbstractFieldNode):

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        assert isinstance(self_obj, Object)
        return self_obj.get_field(self._field_idx)


class FieldWriteNode(_AbstractFieldNode):

    _immutable_fields_ = ["_value_exp?"]
    _child_nodes_      = ["_value_exp"]

    def __init__(self, self_exp, value_exp, field_idx, source_section):
        _AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._value_exp = self.adopt_child(value_exp)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value    = self._value_exp.execute(frame)
        assert isinstance(self_obj, Object)
        assert isinstance(value, AbstractObject)
        self_obj.set_field(self._field_idx, value)
        return value


def create_read_node(self_exp, index, source_section = None):
    return FieldReadNode(self_exp, index, source_section)


def create_write_node(self_exp, value_exp, index, source_section = None):
    return FieldWriteNode(self_exp, value_exp, index, source_section)
