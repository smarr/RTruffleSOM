from .expression_node import ExpressionNode
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object          import Object


class _AbstractFieldNode(ExpressionNode):

    _immutable_fields_ = ["_self_exp?"]
    _child_nodes_      = ["_self_exp"]

    def __init__(self, self_exp, executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._self_exp  = self.adopt_child(self_exp)


class _AbstractUnenforcedFieldReadNode(_AbstractFieldNode):

    def __init__(self, self_exp, source_section = None):
        _AbstractFieldNode.__init__(self, self_exp, False, source_section)

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


class EnforcedFieldReadNode(_AbstractFieldNode):

    _immutable_fields_ = ["_field_idx"]

    ## TODO: consider using the field name instead of the index, to make it nicer...

    def __init__(self, self_exp, field_idx, source_section = None):
        _AbstractFieldNode.__init__(self, self_exp, True, source_section)
        self._field_idx = field_idx ## TODO: should probably convert it already into an SOM Integer

    def execute(self, frame):
        raise RuntimeError("Not yet implemented")

    def execute_void(self, frame):
        raise RuntimeError("Not yet implemented")


class _AbstractFieldWriteNode(_AbstractFieldNode):

    _immutable_fields_ = ["_value_exp?"]
    _child_nodes_      = ["_value_exp"]

    def __init__(self, self_exp, value_exp, executes_enforced, source_section = None):
        _AbstractFieldNode.__init__(self, self_exp, executes_enforced, source_section)
        self._value_exp = self.adopt_child(value_exp)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value    = self._value_exp.execute(frame)
        assert isinstance(self_obj, Object)
        assert isinstance(value, AbstractObject)
        self.write(self_obj, value)
        return value
    
    def execute_void(self, frame):
        self.execute(frame)


class _AbstractUnenforcedFieldWriteNode(_AbstractFieldWriteNode):

    def __init__(self, self_exp, value_exp, source_section = None):
        _AbstractFieldWriteNode.__init__(self, self_exp, value_exp,
                                         False, source_section)


def _make_field_write_node_class(field_idx):
    class _UnenforcedFieldWriteNodeI(_AbstractUnenforcedFieldWriteNode):
        def write(self, self_obj, value):
            return setattr(self_obj, "_field" + str(field_idx), value)
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

    def write(self, self_obj, value):
        self_obj._fields[self._extension_index] = value


class EnforcedFieldWriteNode(_AbstractFieldWriteNode):

    _immutable_fields_ = ["_field_idx"]

    ## TODO: consider using the field name instead of the index, to make it nicer...

    def __init__(self, self_exp, field_idx, value_exp, source_section = None):
        _AbstractFieldWriteNode.__init__(self, self_exp, value_exp, True, source_section)
        self._field_idx = field_idx ## TODO: should probably convert it already into an SOM Integer

    def execute(self, frame):
        raise RuntimeError("Not yet implemented")

    def execute_void(self, frame):
        raise RuntimeError("Not yet implemented")

_field_read_node_classes  = _make_field_read_node_classes(Object.NUMBER_OF_DIRECT_FIELDS)
_field_write_node_classes = _make_field_write_node_classes(Object.NUMBER_OF_DIRECT_FIELDS)


def create_read_node(self_exp_en, self_exp_un, index):
    if index < Object.NUMBER_OF_DIRECT_FIELDS:
        return EnforcedFieldReadNode(self_exp_en, index),\
               _field_read_node_classes[index](self_exp_un)
    else:
        return EnforcedFieldReadNode(self_exp_en, index),\
               UnenforcedFieldReadNodeN(self_exp_un, index - Object.NUMBER_OF_DIRECT_FIELDS)


def create_write_node(self_en, self_un, index, value_en, value_un):
    if index < Object.NUMBER_OF_DIRECT_FIELDS:
        return EnforcedFieldWriteNode(self_en, index, value_en), \
               _field_write_node_classes[index](self_un, value_un)
    else:
        return EnforcedFieldWriteNode(self_en, index, value_en), \
               UnenforcedFieldWriteNodeN(self_un, value_un, index - Object.NUMBER_OF_DIRECT_FIELDS)
