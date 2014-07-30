from rtruffle.node import Node
from som.interpreter.nodes.message_node import AbstractGenericMessageNode, \
    AbstractUninitializedMessageNode
from som.interpreter.nodes.specialized.if_true_false import IfNode, \
    IfTrueIfFalseNode
from som.interpreter.nodes.specialized.to_by_do_node import IntToIntByDoNode, \
    IntToDoubleByDoNode
from som.interpreter.nodes.specialized.to_do_node import IntToIntDoNode, \
    IntToDoubleDoNode
from som.interpreter.nodes.specialized.while_node import WhileMessageNode
from som.vmobjects.domain import request_execution_of_void, request_execution_of, \
    arg_array_to_som_array


_POLYMORPHISM_LIMIT = 6


class UninitializedMessageNodeEnforced(AbstractUninitializedMessageNode):

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        AbstractUninitializedMessageNode.__init__(self, selector, universe,
                                                  rcvr_expr, arg_exprs,
                                                  True, source_section)

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
            GenericMessageNodeEnforced(self._selector, self._universe,
                                       self._rcvr_expr, self._arg_exprs,
                                       self._source_section))


class _AbstractDomainDispatchNode(Node):

    def __init__(self):
        Node.__init__(self, None)


class _CachedDomainDispatchNode(_AbstractDomainDispatchNode):

    _immutable_fields_ = ['_next_in_cache?']
    _child_nodes_      = ['_next_in_cache']

    def __init__(self, next_in_cache):
        _AbstractDomainDispatchNode.__init__(self)
        self._next_in_cache = self.adopt_child(next_in_cache)


class _UninitializedDomainDispatchNode(_AbstractDomainDispatchNode):

    _immutable_fields_ = ['_universe', '_selector', '_super_class']

    def __init__(self, selector, universe, super_class):
        _AbstractDomainDispatchNode.__init__(self)
        self._selector    = selector
        self._universe    = universe
        self._super_class = super_class

    def _chain_depth(self):
        depth = 0
        current = self
        while isinstance(current, _AbstractDomainDispatchNode):
            depth += 1
            current = current.get_parent()
        return depth

    def _specialize(self, rcvr):
        if self._chain_depth() == _POLYMORPHISM_LIMIT:
            return self.replace(_GenericDomainDispatchNode(self._selector,
                                                           self._super_class,
                                                           self._universe))

        uninitialized = _UninitializedDomainDispatchNode(self._selector,
                                                         self._universe,
                                                         self._super_class)

        rcvr_domain = rcvr.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(None)
        if rcvr_domain_class is self._universe.domainClass:

            if self._super_class is not None:
                node = _StandardDomainSuperDispatchNode(
                    uninitialized, self._selector, self._universe.domainClass,
                    self._universe, self._super_class)
            else:
                node = _StandardDomainDispatchNode(
                    uninitialized, self._selector, self._universe.domainClass,
                    self._universe)
            return self.replace(node)
        else:
            return self.replace(_CachedDomainHandlerDispatchNode(
                self._selector, rcvr_domain_class, self._super_class,
                self._universe, uninitialized))

    def dispatch_void(self, frame, rcvr, args):
        self._specialize(rcvr).dispatch_void(frame, rcvr, args)

    def dispatch(self, frame, rcvr, args):
        return self._specialize(rcvr).dispatch(frame, rcvr, args)


class _StandardDomainDispatchNode(_CachedDomainDispatchNode):

    _immutable_fields_ = ['_standard_domain_class', '_universe', '_selector']

    def __init__(self, next_in_cache, selector, standard_domain_class, universe):
        _CachedDomainDispatchNode.__init__(self, next_in_cache)
        self._standard_domain_class = standard_domain_class
        self._universe        = universe
        self._selector        = selector

    def _get_rcvr_class(self, rcvr):
        return rcvr.get_class(self._universe)

    def _do_dispatch_void(self, args, frame, rcvr, rcvr_class):
        method = rcvr_class.lookup_invokable(self._selector)
        if method:
            method.invoke_enforced_void(rcvr, args,
                                        frame.get_executing_domain())
        else:
            rcvr.send_does_not_understand_enforced_void(
                self._selector, args, self._universe,
                frame.get_executing_domain())

    def _do_dispatch(self, args, frame, rcvr, rcvr_class):
        method = rcvr_class.lookup_invokable(self._selector)
        if method:
            return method.invoke_enforced(rcvr, args,
                                          frame.get_executing_domain())
        else:
            return rcvr.send_does_not_understand_enforced(
                self._selector, args, self._universe,
                frame.get_executing_domain())

    def dispatch_void(self, frame, rcvr, args):
        rcvr_domain = rcvr.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(self._universe)

        if rcvr_domain_class is self._standard_domain_class:
            rcvr_class = self._get_rcvr_class(rcvr)
            self._do_dispatch_void(args, frame, rcvr, rcvr_class)
        else:
            self._next_in_cache.dispatch_void(frame, rcvr, args)

    def dispatch(self, frame, rcvr, args):
        rcvr_domain = rcvr.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(self._universe)

        if rcvr_domain_class is self._standard_domain_class:
            rcvr_class = self._get_rcvr_class(rcvr)
            return self._do_dispatch(args, frame, rcvr, rcvr_class)
        else:
            return self._next_in_cache.dispatch(frame, rcvr, args)


class _StandardDomainSuperDispatchNode(_StandardDomainDispatchNode):

    _immutable_fields_ = ['_super_class']

    def __init__(self, next_in_cache, selector, standard_domain_class, universe,
                 super_class):
        _StandardDomainDispatchNode.__init__(self, next_in_cache, selector,
                                             standard_domain_class, universe)
        self._super_class = super_class

    def _get_rcvr_class(self, rcvr):
        return self._super_class


class _CachedDomainHandlerDispatchNode(_CachedDomainDispatchNode):

    _immutable_fields_ = ['_intersession_handler', '_domain_class',
                          '_super_class', '_universe', '_baselevel_selector']

    def __init__(self, baselevel_selector, domain_class, super_class, universe,
                 next_in_cache):
        _CachedDomainDispatchNode.__init__(self, next_in_cache)

        selector = universe.symbol_for("requestExecutionOf:with:on:lookup:")
        self._intersession_handler = domain_class.lookup_invokable(selector)

        self._domain_class = domain_class
        self._super_class  = super_class
        self._universe     = universe
        self._baselevel_selector = baselevel_selector

    def _get_rcvr_class(self, rcvr):
        if self._super_class is not None:
            return self._super_class
        return rcvr.get_class(self._universe)

    def _is_cached_domain(self, rcvr):
        rcvr_domain = rcvr.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(self._universe)
        return rcvr_domain_class is self._domain_class

    def dispatch_void(self, frame, rcvr, args):
        if self._is_cached_domain(rcvr):
            rcvr_domain = rcvr.get_domain(self._universe)
            som_args = arg_array_to_som_array(args, rcvr_domain, self._universe)
            self._intersession_handler.invoke_unenforced_void(
                rcvr_domain, [self._baselevel_selector, som_args, rcvr,
                              self._get_rcvr_class(rcvr)],
                frame.get_executing_domain())
        else:
            self._next_in_cache.dispatch_void(frame, rcvr, args)

    def dispatch(self, frame, rcvr, args):
        if self._is_cached_domain(rcvr):
            rcvr_domain = rcvr.get_domain(self._universe)
            som_args = arg_array_to_som_array(args, rcvr_domain, self._universe)
            return self._intersession_handler.invoke_unenforced(
                rcvr_domain, [self._baselevel_selector, som_args, rcvr,
                              self._get_rcvr_class(rcvr)],
                frame.get_executing_domain())
        else:
            return self._next_in_cache.dispatch(frame, rcvr, args)


class _GenericDomainDispatchNode(_AbstractDomainDispatchNode):

    _immutable_fields_ = ['_selector', '_super_class', '_universe']

    def __init__(self, selector, super_class, universe):
        _AbstractDomainDispatchNode.__init__(self)
        self._selector    = selector
        self._super_class = super_class
        self._universe    = universe

    def _class_of_receiver(self, rcvr):
        if self._super_class:
            return self._super_class
        return rcvr.get_class(self._universe)

    def dispatch_void(self, frame, rcvr, args):
        return request_execution_of_void(self._selector,
                                         rcvr, args,
                                         self._class_of_receiver(rcvr),
                                         self._universe,
                                         frame.get_executing_domain())

    def dispatch(self, frame, rcvr, args):
        return request_execution_of(self._selector,
                                    rcvr, args,
                                    self._class_of_receiver(rcvr),
                                    self._universe,
                                    frame.get_executing_domain())


class GenericMessageNodeEnforced(AbstractGenericMessageNode):

    _immutable_fields_ = ['_dispatch?']
    _child_nodes_      = ['_dispatch']

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        AbstractGenericMessageNode.__init__(self, selector, universe, rcvr_expr,
                                            arg_exprs, True, source_section)
        if rcvr_expr.is_super_node():
            super_class = rcvr_expr.get_super_class()
        else:
            super_class = None
        self._dispatch = self.adopt_child(_UninitializedDomainDispatchNode(
            selector, universe, super_class))

    def execute_evaluated_void(self, frame, rcvr, args):
        assert args is not None
        return self._dispatch.dispatch_void(frame, rcvr, args)

    def execute_evaluated(self, frame, rcvr, args):
        assert args is not None
        return self._dispatch.dispatch(frame, rcvr, args)
