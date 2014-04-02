from som.vmobjects.block   import Block
from som.vmobjects.double  import Double
from som.vmobjects.integer import Integer
from som.vmobjects.method  import Method

from .to_do_node       import AbstractToDoNode

from rpython.rlib import jit


class AbstractToByDoNode(AbstractToDoNode):

    _immutable_fields_ = ['_step_expr?']
    _child_nodes_      = ['_step_expr' ]

    def __init__(self, rcvr_expr, limit_expr, step_expr, body_expr, universe,
                 executes_enforced, source_section = None):
        AbstractToDoNode.__init__(self, rcvr_expr, limit_expr, body_expr,
                                  universe, executes_enforced, source_section)
        self._step_expr  = self.adopt_child(step_expr)

    def execute(self, frame):
        rcvr  = self._rcvr_expr.execute(frame)
        limit = self._limit_expr.execute(frame)
        step  = self._step_expr.execute(frame)
        body  = self._body_expr.execute(frame)
        self._to_by_loop_void(rcvr, limit, step, body)
        return rcvr
    
    def execute_void(self, frame):
        self.execute(frame)

    def execute_evaluated(self, frame, rcvr, args):
        self._to_by_loop_void(rcvr, args[0], args[1], args[2])
        return rcvr
    
    def execute_evaluated_void(self, frame, rcvr, args):
        self._to_by_loop_void(rcvr, args[0], args[1], args[2])


def get_printable_location(block_method):
    assert isinstance(block_method, Method)
    return "#to:do: %s" % block_method.merge_point_string()


int_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntToIntByDoNode(AbstractToByDoNode):

    def _to_by_loop_void(self, rcvr, limit, step, body_block):
        block_method = body_block.get_method()

        i   = rcvr.get_embedded_integer()
        top = limit.get_embedded_integer()
        by  = step.get_embedded_integer()
        while i <= top:
            int_driver.jit_merge_point(block_method = block_method)
            block_method.invoke(body_block,
                                [self._universe.new_integer(i)])
            i += by

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Integer) and isinstance(rcvr, Integer) and
                len(args) == 3 and isinstance(args[1], Integer) and
                isinstance(args[2], Block) and
                selector.get_string() == "to:by:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntToIntByDoNode(node._rcvr_expr, node._arg_exprs[0],
                             node._arg_exprs[1], node._arg_exprs[2],
                             node._universe, node._executes_enforced,
                             node._source_section))

double_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntToDoubleByDoNode(AbstractToByDoNode):

    def _to_by_loop_void(self, rcvr, limit, step, body_block):
        block_method = body_block.get_method()

        i   = rcvr.get_embedded_integer()
        top = limit.get_embedded_double()
        by  = step.get_embedded_integer()
        while i <= top:
            double_driver.jit_merge_point(block_method = block_method)
            block_method.invoke(body_block,
                                [self._universe.new_integer(i)])
            i += by

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Double) and isinstance(rcvr, Integer) and
                len(args) == 3 and isinstance(args[1], Integer) and
                isinstance(args[2], Block) and
                selector.get_string() == "to:by:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntToDoubleByDoNode(node._rcvr_expr, node._arg_exprs[0],
                                node._arg_exprs[1], node._arg_exprs[2],
                                node._universe,
                                node._executes_enforced, node._source_section))