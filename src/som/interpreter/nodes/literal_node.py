from .expression_node import ExpressionNode


class LiteralNode(ExpressionNode):

    _immutable_fields_ = ["_value"]

    def __init__(self, value, executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._value = value

    def execute(self, frame):
        return self._value

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free
