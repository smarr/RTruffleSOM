from .expression_node     import ExpressionNode
from ...vmobjects.double  import Double
from ...vmobjects.string  import String
from ...vmobjects.integer import Integer


class LiteralNode(ExpressionNode):

    _immutable_fields_ = ["_value"]

    def __init__(self, value, source_section = None):
        ExpressionNode.__init__(self, source_section)
        self._value = value

    def execute(self, frame):
        return self._value

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free


class LiteralIntegerNode(LiteralNode):

    _immutable_fields_ = ["_int_value"]

    def __init__(self, value, source_section = None):
        LiteralNode.__init__(self, value, source_section)
        assert isinstance(value, Integer)
        self._int_value = value.get_embedded_integer()

    def execute_int(self, frame):
        return self._int_value


class LiteralStringNode(LiteralNode):

    _immutable_fields_ = ['_string_value']

    def __init__(self, value, source_section = None):
        LiteralNode.__init__(self, value, source_section)
        assert isinstance(value, String)
        self._string_value = value.get_embedded_string()

    def execute_string(self, frame):
        return self._string_value


class LiteralDoubleNode(LiteralNode):

    _immutable_fields_ = ['_float_value']

    def __init__(self, value, source_section = None):
        LiteralNode.__init__(self, value, source_section)
        assert isinstance(value, Double)
        self._float_value = value.get_embedded_double()

    def execute_float(self, frame):
        return self._float_value
