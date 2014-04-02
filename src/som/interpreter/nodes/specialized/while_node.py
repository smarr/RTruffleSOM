from rpython.rlib import jit

from ..expression_node import ExpressionNode

from som.vmobjects.block  import Block
from som.vmobjects.method import Method


class AbstractWhileMessageNode(ExpressionNode):

    _immutable_fields_ = ['_predicate_bool', '_rcvr_expr?', '_body_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr', '_body_expr']

    def __init__(self, rcvr_expr, body_expr, predicate_bool_obj, universe,
                 executes_enforced, source_section):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._predicate_bool = predicate_bool_obj
        self._rcvr_expr      = self.adopt_child(rcvr_expr)
        self._body_expr      = self.adopt_child(body_expr)
        self._universe       = universe

    def execute(self, frame):
        self.execute_void(frame)
        return self._universe.nilObject

    def execute_void(self, frame):
        rcvr_value = self._rcvr_expr.execute(frame)
        body_block = self._body_expr.execute(frame)

        self._do_while(rcvr_value, body_block, frame.get_executing_domain())

# STEFAN: SOM doesn't actually have #whileTrue:, #whileFalse: for booleans.

# def get_printable_location_while_value(body_method, node):
#     assert isinstance(body_method, Method)
#     return "while_value: %s" % body_method.merge_point_string()
#
# while_value_driver = jit.JitDriver(
#     greens=['body_method', 'node'], reds='auto',
#     get_printable_location = get_printable_location_while_value)
#
#
# class WhileWithValueReceiver(AbstractWhileMessageNode):
#
#     def execute_evaluated(self, frame, rcvr_value, body_block):
#         if rcvr_value is not self._predicate_bool:
#             return self._universe.nilObject
#         body_method = body_block.get_method()
#
#         while True:
#             while_value_driver.jit_merge_point(body_method = body_method,
#                                                node        = self)
#             body_method.invoke(body_block, None)


def get_printable_location_while(body_method, condition_method, while_type):
    assert isinstance(condition_method, Method)
    assert isinstance(body_method, Method)

    return "%s while %s: %s" % (condition_method.merge_point_string(),
                                while_type,
                                body_method.merge_point_string())


while_driver = jit.JitDriver(
    greens=['body_method', 'condition_method', 'node'], reds='auto',
    get_printable_location = get_printable_location_while)


class WhileMessageNode(AbstractWhileMessageNode):

    def execute_evaluated(self, frame, rcvr, args):
        self.execute_evaluated_void(frame, rcvr, args)
        return self._universe.nilObject

    def execute_evaluated_void(self, frame, rcvr, args):
        self._do_while(rcvr, args[0], frame.get_executing_domain())

    def _do_while(self, rcvr_block, body_block, domain):
        condition_method = rcvr_block.get_method()
        body_method      = body_block.get_method()

        while True:
            while_driver.jit_merge_point(body_method     = body_method,
                                         condition_method= condition_method,
                                         node            = self)

            if self._executes_enforced:
                condition_value = condition_method.invoke_enforced(rcvr_block, None, domain)
            else:
                condition_value = condition_method.invoke_unenforced(rcvr_block, None, domain)

            if condition_value is not self._predicate_bool:
                break

            if self._executes_enforced:
                body_method.invoke_enforced_void(body_block, None, domain)
            else:
                body_method.invoke_unenforced_void(body_block, None, domain)


    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        sel = selector.get_string()
        return isinstance(args[0], Block) and (sel == "whileTrue:" or
                                               sel == "whileFalse:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        sel = selector.get_string()
        if sel == "whileTrue:":
            return node.replace(
                WhileMessageNode(node._rcvr_expr, node._arg_exprs[0],
                                 node._universe.trueObject,
                                 node._universe,
                                 node._executes_enforced,
                                 node._source_section))
        else:
            assert sel == "whileFalse:"
            return node.replace(
                WhileMessageNode(node._rcvr_expr, node._arg_exprs[0],
                                 node._universe.falseObject,
                                 node._universe,
                                 node._executes_enforced,
                                 node._source_section))
