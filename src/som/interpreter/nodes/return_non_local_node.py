from .contextual_node import ContextualNode
from .expression_node import ExpressionNode

from ..control_flow   import ReturnException


class ReturnNonLocalNode(ContextualNode):

    _immutable_fields_ = ['_expr?', '_universe']
    _child_nodes_      = ['_expr']

    def __init__(self, context_level, expr, universe, executes_enforced, source_section = None):
        ContextualNode.__init__(self, context_level, executes_enforced, source_section)
        self._expr     = self.adopt_child(expr)
        self._universe = universe

    def execute(self, frame):
        ctx_frame = self.determine_context(frame)

        if ctx_frame.is_on_stack():
            result = self._expr.execute(frame)
            raise ReturnException(result, ctx_frame)
        else:
            block      = frame.get_self()
            outer_self = ctx_frame.get_self()
            if self._executes_enforced:
                return outer_self.send_escaped_block_enforced(block,
                                                              self._universe,
                                                              frame.get_executing_domain())
            else:
                return outer_self.send_escaped_block_unenforced(block,
                                                                self._universe,
                                                                frame.get_executing_domain())

    def execute_void(self, frame):
        self.execute(frame)


class CatchNonLocalReturnNode(ExpressionNode):

    _immutable_fields_ = ['_method_body?']
    _child_nodes_      = ['_method_body']

    def __init__(self, method_body, executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._method_body = self.adopt_child(method_body)

    def execute(self, frame):
        try:
            result = self._method_body.execute(frame)
        except ReturnException as e:
            if not e.has_reached_target(frame):
                raise e
            else:
                return e.get_result()
        finally:
            frame.mark_as_no_longer_on_stack()
        return result

    def execute_void(self, frame):
        try:
            self._method_body.execute_void(frame)
        except ReturnException as e:
            if not e.has_reached_target(frame):
                raise e
        finally:
            frame.mark_as_no_longer_on_stack()
