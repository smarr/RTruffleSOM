from .expression_node import ExpressionNode

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.domain import read_field_of, write_to_field_of
from som.vmobjects.object          import Object


class AbstractFieldNode(ExpressionNode):

    _immutable_fields_ = ["_self_exp?"]
    _child_nodes_      = ["_self_exp"]

    def __init__(self, self_exp, executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._self_exp  = self.adopt_child(self_exp)


class _AbstractUnenforcedFieldReadNode(AbstractFieldNode):

    def __init__(self, self_exp, source_section = None):
        AbstractFieldNode.__init__(self, self_exp, False, source_section)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        assert isinstance(self_obj, Object)
        return self.read(self_obj)
    
    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free


def _make_field_read_node_class(field_idx):
    class _UnenforcedFieldReadNodeI(_AbstractUnenforcedFieldReadNode):
        def read(self, self_obj):
            return getattr(self_obj, "_field" + str(field_idx))
    return _UnenforcedFieldReadNodeI


def _make_field_read_node_classes(count):
    return [_make_field_read_node_class(i + 1) for i in range(count)]


class UnenforcedFieldReadNodeN(_AbstractUnenforcedFieldReadNode):
    
    _immutable_fields_ = ["_extension_index"]
    
    def __init__(self, self_exp, extension_index, source_section = None):
        _AbstractUnenforcedFieldReadNode.__init__(self, self_exp,
                                                  source_section)
        assert extension_index >= 0
        self._extension_index = extension_index

    def read(self, self_obj):
        return self_obj._fields[self._extension_index]


class AbstractFieldWriteNode(AbstractFieldNode):

    _immutable_fields_ = ["_value_exp?"]
    _child_nodes_      = ["_value_exp"]

    def __init__(self, self_exp, value_exp, executes_enforced, source_section = None):
        AbstractFieldNode.__init__(self, self_exp, executes_enforced, source_section)
        self._value_exp = self.adopt_child(value_exp)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value    = self._value_exp.execute(frame)
        assert isinstance(self_obj, Object)
        assert isinstance(value, AbstractObject)
        self.write(frame, self_obj, value)
        return value
    
    def execute_void(self, frame):
        self.execute(frame)


class _AbstractUnenforcedFieldWriteNode(AbstractFieldWriteNode):

    def __init__(self, self_exp, value_exp, source_section = None):
        AbstractFieldWriteNode.__init__(self, self_exp, value_exp,
                                         False, source_section)


def _make_field_write_node_class(field_idx):
    class _UnenforcedFieldWriteNodeI(_AbstractUnenforcedFieldWriteNode):
        def write(self, frame, self_obj, value):
            setattr(self_obj, "_field" + str(field_idx), value)
            return value
    return _UnenforcedFieldWriteNodeI


def _make_field_write_node_classes(count):
    return [_make_field_write_node_class(i + 1) for i in range(count)]

    
class UnenforcedFieldWriteNodeN(_AbstractUnenforcedFieldWriteNode):
    
    _immutable_fields_ = ["_extension_index"]
    
    def __init__(self, self_exp, value_exp, extension_index, source_section = None):
        _AbstractUnenforcedFieldWriteNode.__init__(self, self_exp, value_exp,
                                                   source_section)
        assert extension_index >= 0
        self._extension_index = extension_index

    def write(self, frame, self_obj, value):
        self_obj._fields[self._extension_index] = value


_field_read_node_classes  = _make_field_read_node_classes(Object.NUMBER_OF_DIRECT_FIELDS)
_field_write_node_classes = _make_field_write_node_classes(Object.NUMBER_OF_DIRECT_FIELDS)


def get_read_node_class(field_idx):
    return _field_read_node_classes[field_idx]


def get_write_node_class(field_idx):
    return _field_write_node_classes[field_idx]
