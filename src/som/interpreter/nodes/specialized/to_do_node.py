from ..expression_node import ExpressionNode
from rpython.rlib import jit
from som.vmobjects.block import Block
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer
from som.vmobjects.method import Method


class AbstractToDoNode(ExpressionNode):

    _immutable_fields_ = ['_rcvr_expr?', '_limit_expr?', '_body_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr', '_limit_expr', '_body_expr']

    def __init__(self, rcvr_expr, limit_expr, body_expr, universe,
                 executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._rcvr_expr  = self.adopt_child(rcvr_expr)
        self._limit_expr = self.adopt_child(limit_expr)
        self._body_expr  = self.adopt_child(body_expr)
        self._universe   = universe

    def execute(self, frame):
        rcvr  = self._rcvr_expr.execute(frame)
        limit = self._limit_expr.execute(frame)
        body  = self._body_expr.execute(frame)
        self._do_loop(rcvr, limit, body, frame.get_executing_domain())
        return rcvr

    def execute_void(self, frame):
        rcvr  = self._rcvr_expr.execute(frame)
        limit = self._limit_expr.execute(frame)
        body  = self._body_expr.execute(frame)
        self._do_loop(rcvr, limit, body, frame.get_executing_domain())

    def execute_evaluated(self, frame, rcvr, args):
        self._do_loop(rcvr, args[0], args[1], frame.get_executing_domain())
        return rcvr

    def execute_evaluated_void(self, frame, rcvr, args):
        self._do_loop(rcvr, args[0], args[1], frame.get_executing_domain())


def get_printable_location(block_method):
    assert isinstance(block_method, Method)
    return "#to:do: %s" % block_method.merge_point_string()


int_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntToIntDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block, domain):
        block_method = body_block.get_method()

        i   = rcvr.get_embedded_integer()
        top = limit.get_embedded_integer()
        while i <= top:
            int_driver.jit_merge_point(block_method = block_method)
            if self._executes_enforced:
                block_method.invoke_enforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            else:
                block_method.invoke_unenforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            i += 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Integer) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], Block) and
                selector.get_string() == "to:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntToIntDoNode(node._rcvr_expr, node._arg_exprs[0],
                           node._arg_exprs[1], node._universe,
                           node._executes_enforced,
                           node._source_section))


double_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntToDoubleDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block, domain):
        block_method = body_block.get_method()

        i   = rcvr.get_embedded_integer()
        top = limit.get_embedded_double()
        while i <= top:
            double_driver.jit_merge_point(block_method = block_method)
            if self._executes_enforced:
                block_method.invoke_enforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            else:
                block_method.invoke_unenforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            i += 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Double) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], Block) and
                selector.get_string() == "to:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntToDoubleDoNode(node._rcvr_expr, node._arg_exprs[0],
                              node._arg_exprs[1], node._universe,
                              node._executes_enforced,
                              node._source_section))
