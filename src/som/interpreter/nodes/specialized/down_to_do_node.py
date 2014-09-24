from ..expression_node import ExpressionNode
from rpython.rlib import jit
from som.interpreter.nodes.specialized.to_do_node import AbstractToDoNode
from som.vmobjects.block import Block
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer
from som.vmobjects.method import Method


def get_printable_location(block_method):
    assert isinstance(block_method, Method)
    return "#to:do: %s" % block_method.merge_point_string()


int_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntDownToIntDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block, domain):
        block_method = body_block.get_method()

        i      = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_integer()
        while i >= bottom:
            int_driver.jit_merge_point(block_method = block_method)
            if self._executes_enforced:
                block_method.invoke_enforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            else:
                block_method.invoke_unenforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Integer) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], Block) and
                selector.get_string() == "downTo:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntDownToIntDoNode(node._rcvr_expr, node._arg_exprs[0],
                               node._arg_exprs[1], node._universe,
                               node._executes_enforced,
                               node._source_section))


double_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntDownToDoubleDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block, domain):
        block_method = body_block.get_method()

        i      = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_double()
        while i >= bottom:
            double_driver.jit_merge_point(block_method = block_method)
            if self._executes_enforced:
                block_method.invoke_enforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            else:
                block_method.invoke_unenforced_void(
                    body_block, [self._universe.new_integer(i)], domain)
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Double) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], Block) and
                selector.get_string() == "downTo:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntDownToDoubleDoNode(node._rcvr_expr, node._arg_exprs[0],
                                  node._arg_exprs[1], node._universe,
                                  node._executes_enforced,
                                  node._source_section))
