from rpython.rlib import jit

from ..expression_node import ExpressionNode

from ....vmobjects.block  import Block
from ....vmobjects.method import Method


def get_printable_location(body_method, condition_method, node):
    assert isinstance(condition_method, Method)
    assert isinstance(body_method, Method)

    return "%s repeatUntil: %s" % (condition_method.merge_point_string(),
                                   body_method.merge_point_string())


repeat_driver = jit.JitDriver(
    greens=['body_method', 'condition_method', 'node'], reds='auto',
    get_printable_location = get_printable_location)


class RepeatUntilNode(ExpressionNode):

    _immutable_fields_ = ['_rcvr_expr?', '_body_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr', '_body_expr']

    def __init__(self, rcvr_expr, body_expr, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr      = self.adopt_child(rcvr_expr)
        self._body_expr      = self.adopt_child(body_expr)
        self._universe       = universe

    def execute(self, frame):
        rcvr_value = self._rcvr_expr.execute(frame)
        body_block = self._body_expr.execute(frame)

        self._do_loop(rcvr_value, body_block)
        return self._universe.nilObject

    def execute_evaluated(self, frame, rcvr, args):
        self._do_loop(rcvr, args[0])
        return self._universe.nilObject

    def _do_loop(self, rcvr_block, body_block):
        body_method      = rcvr_block.get_method()
        condition_method = body_block.get_method()

        if rcvr_block.is_same_context(body_block):
            rcvr_block = body_block

        while True:
            repeat_driver.jit_merge_point(body_method     = body_method,
                                          condition_method= condition_method,
                                          node            = self)

            # STEFAN: looks stupid but might help the jit
            if rcvr_block is body_block:
                rcvr_block = body_block

            body_method.invoke(body_block, [])
            condition_value = condition_method.invoke(rcvr_block, [])
            if condition_value is self._universe.trueObject:
                break

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        sel = selector.get_string()
        return isinstance(rcvr, Block) and \
               isinstance(args[0], Block) and \
               (sel == "repeatUntil:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            RepeatUntilNode(node._rcvr_expr, node._arg_exprs[0],
                            node._universe, node._source_section))
