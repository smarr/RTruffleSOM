from ..expression_node import ExpressionNode
from som.vm.globals import nilObject, falseObject, trueObject

from ....vmobjects.block  import Block


class AbstractWhileMessageNode(ExpressionNode):

    _immutable_fields_ = ['_predicate_bool', '_rcvr_expr?', '_body_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr', '_body_expr']

    def __init__(self, rcvr_expr, body_expr, predicate_bool_obj, universe,
                 source_section):
        ExpressionNode.__init__(self, source_section)
        self._predicate_bool = predicate_bool_obj
        self._rcvr_expr      = self.adopt_child(rcvr_expr)
        self._body_expr      = self.adopt_child(body_expr)
        self._universe       = universe

    def execute(self, frame):
        rcvr_value = self._rcvr_expr.execute(frame)
        body_block = self._body_expr.execute(frame)

        self._do_while(rcvr_value, body_block)
        return nilObject

# class WhileWithValueReceiver(AbstractWhileMessageNode):
#
#     def execute_evaluated(self, frame, rcvr_value, body_block):
#         if rcvr_value is not self._predicate_bool:
#             return nilObject
#         body_method = body_block.get_method()
#
#         while True:
#             while_value_driver.jit_merge_point(body_method = body_method,
#                                                node        = self)
#             body_method.invoke(body_block, None)


class WhileMessageNode(AbstractWhileMessageNode):

    def execute_evaluated(self, frame, rcvr, args):
        self._do_while(rcvr, args[0])
        return nilObject

    def _do_while(self, rcvr_block, body_block):
        condition_method = rcvr_block.get_method()
        body_method      = body_block.get_method()

        if rcvr_block.is_same_context(body_block):
            rcvr_block = body_block

        while True:
            condition_value = condition_method.invoke(rcvr_block, [])
            if condition_value is not self._predicate_bool:
                break
            body_method.invoke(body_block, [])

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        sel = selector.get_string()
        return isinstance(args[0], Block) and sel == "whileTrue:"

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            WhileMessageNode(node._rcvr_expr, node._arg_exprs[0],
                             trueObject,
                             node._universe, node._source_section))
