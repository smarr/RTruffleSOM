from .expression_node import ExpressionNode
from som.vmobjects.abstract_object import AbstractObject

from .specialized.if_true_false import IfTrueIfFalseNode, IfNode
from .specialized.to_do_node    import IntToIntDoNode, IntToDoubleDoNode
from .specialized.to_by_do_node import IntToIntByDoNode, IntToDoubleByDoNode
from .specialized.while_node    import WhileMessageNode

from rpython.rlib.jit import unroll_safe


class AbstractMessageNode(ExpressionNode):

    _immutable_fields_ = ['_selector', '_universe',
                          '_rcvr_expr?', '_arg_exprs?[*]']
    _child_nodes_      = ['_rcvr_expr',  '_arg_exprs[*]']

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._selector = selector
        self._universe = universe
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._arg_exprs = self.adopt_children(arg_exprs)

    @unroll_safe
    def _evaluate_rcvr_and_args(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        assert isinstance(rcvr, AbstractObject)
        if self._arg_exprs:
            args = [arg_exp.execute(frame) for arg_exp in self._arg_exprs]
        else:
            args = None
        return rcvr, args


class AbstractUninitializedMessageNode(AbstractMessageNode):

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self._specialize(rcvr, args).execute_evaluated(frame, rcvr, args)

    def execute_void(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        self._specialize(rcvr, args).execute_evaluated_void(frame, rcvr, args)


class UninitializedMessageNodeUnenforced(AbstractUninitializedMessageNode):

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        AbstractUninitializedMessageNode.__init__(self, selector, universe,
                                                  rcvr_expr, arg_exprs,
                                                  False, source_section)

    def _specialize(self, rcvr, args):
        if args:
            for specialization in [WhileMessageNode,
                                   IntToIntDoNode,   IntToDoubleDoNode,
                                   IntToIntByDoNode, IntToDoubleByDoNode,
                                   IfTrueIfFalseNode,
                                   IfNode]:
                if specialization.can_specialize(self._selector, rcvr, args,
                                                 self):
                    return specialization.specialize_node(self._selector, rcvr,
                                                          args, self)
        return self.replace(
            GenericMessageNodeUnenforced(self._selector, self._universe,
                                         self._rcvr_expr, self._arg_exprs,
                                         self._source_section))


class AbstractGenericMessageNode(AbstractMessageNode):

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self.execute_evaluated(frame, rcvr, args)

    def execute_void(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        self.execute_evaluated_void(frame, rcvr, args)

    def _lookup_method(self, rcvr):
        rcvr_class = self._class_of_receiver(rcvr)
        return rcvr_class.lookup_invokable(self._selector)

    def _class_of_receiver(self, rcvr):
        if self._rcvr_expr.is_super_node():
            return self._rcvr_expr.get_super_class()
        return rcvr.get_class(self._universe)

    def __str__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               self._selector,
                               self._source_section)


class GenericMessageNodeUnenforced(AbstractGenericMessageNode):

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        AbstractGenericMessageNode.__init__(self, selector, universe, rcvr_expr,
                                            arg_exprs, False, source_section)

    def execute_evaluated_void(self, frame, rcvr, args):
        method = self._lookup_method(rcvr)
        if method:
            method.invoke_unenforced_void(rcvr, args,
                                          frame.get_executing_domain())
        else:
            rcvr.send_does_not_understand_unenforced_void(
                self._selector, args, self._universe,
                frame.get_executing_domain())

    def execute_evaluated(self, frame, rcvr, args):
        method = self._lookup_method(rcvr)
        if method:
            result = method.invoke_unenforced(rcvr, args,
                                              frame.get_executing_domain())
        else:
            result = rcvr.send_does_not_understand_unenforced(
                self._selector, args, self._universe,
                frame.get_executing_domain())
        assert isinstance(result, AbstractObject)
        return result
