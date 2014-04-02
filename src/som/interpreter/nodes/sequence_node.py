from .expression_node import ExpressionNode

from rpython.rlib.jit import unroll_safe


class SequenceNode(ExpressionNode):

    _immutable_fields_ = ['_exprs?[*]']
    _child_nodes_      = ['_exprs[*]']

    def __init__(self, expressions, executes_enforced, source_section):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._exprs = self.adopt_children(expressions)

    def execute(self, frame):
        self._execute_all_but_last(frame)
        return self._exprs[-1].execute(frame)

    @unroll_safe
    def _execute_all_but_last(self, frame):
        for i in range(0, len(self._exprs) - 1):
            self._exprs[i].execute_void(frame)

    def execute_void(self, frame):
        self._execute_all_but_last(frame)
        self._exprs[-1].execute_void(frame)
