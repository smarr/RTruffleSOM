from rtruffle.node import Node
from som.interpreter.nodes.expression_node import ExpressionNode
from som.interpreter.nodes.global_read_node import \
    AbstractUninitializedGlobalReadNode
from som.vmobjects.domain import read_global


_POLYMORPHISM_LIMIT = 6


class _AbstractUninitializedEnforced(AbstractUninitializedGlobalReadNode):

    def _chain_depth(self):
        depth = 0
        current = self
        while isinstance(current, AbstractUninitializedGlobalReadNode)\
                or isinstance(current, _CachedEnforced):
            depth += 1
            current = current.get_parent()
        return depth


class UninitializedGlobalReadNodeEnforced(_AbstractUninitializedEnforced):

    def __init__(self, global_name, universe, source_section = None):
        _AbstractUninitializedEnforced.__init__(self, global_name, universe,
                                                True, source_section)

    def execute(self, frame):
        return self._specialize(frame.get_executing_domain()).execute(frame)

    def execute_void(self, frame):
        self.execute(frame)

    def _specialize(self, executing_domain):
        if self._chain_depth() == _POLYMORPHISM_LIMIT:
            return self.replace(_GenericEnforced(self._global_name,
                                                 self._universe,
                                                 True,
                                                 self._source_section))

        uninitialized = UninitializedGlobalReadNodeEnforced(
            self._global_name, self._universe, self._source_section)
        domain_class = executing_domain.get_class(self._universe)

        if executing_domain is self._universe.standardDomain:
            return self.replace(_StandardDomainUncached(self._global_name,
                                                        domain_class,
                                                        uninitialized,
                                                        self._universe,
                                                        self._source_section))

        return self.replace(_CachedEnforced(self._global_name, domain_class,
                                            uninitialized, self._universe,
                                            self._source_section))


class _CachedEnforced(AbstractUninitializedGlobalReadNode):

    _immutable_fields_ = ['_domain_class', '_next_in_cache?',
                          '_intercession_handler']
    _child_nodes_      = ['_next_in_cache']

    def __init__(self, global_name, domain_class, next_in_cache, universe,
                 source_section):
        AbstractUninitializedGlobalReadNode.__init__(self, global_name,
                                                     universe, True,
                                                     source_section)
        self._domain_class  = domain_class
        self._next_in_cache = self.adopt_child(next_in_cache)

        selector = universe.symbol_for("readGlobal:for:")
        handler = domain_class.lookup_invokable(selector)
        assert handler is not None
        self._intercession_handler = handler

    def _is_cached_domain(self, frame):
        executing_domain = frame.get_executing_domain()
        executing_domain_class = executing_domain.get_class(self._universe)
        return self._domain_class is executing_domain_class

    def execute(self, frame):
        if self._is_cached_domain(frame):
            executing_domain = frame.get_executing_domain()
            return self._intercession_handler.invoke_unenforced(
                executing_domain, [self._global_name], executing_domain)
        else:
            return self._next_in_cache.execute(frame)


class _StandardDomainUncached(_CachedEnforced):

    def execute(self, frame):
        if self._is_cached_domain(frame):
            if self._universe.has_global(self._global_name):
                return self._specialize().execute(frame)
            else:
                return frame.get_self().send_unknown_global_enforced(
                    self._global_name, self._universe,
                    frame.get_executing_domain())
        else:
            return self._next_in_cache.execute(frame)

    def _specialize(self):
        return self.replace(_StandardDomainCached(self._global_name,
                                                  self._domain_class,
                                                  self._next_in_cache,
                                                  self._universe,
                                                  self._source_section))


class _StandardDomainCached(_CachedEnforced):

    _immutable_fields_ = ['_assoc']

    def __init__(self, global_name, domain_class, next_in_cache, universe,
                 source_section):
        _CachedEnforced.__init__(self, global_name, domain_class, next_in_cache,
                                 universe, source_section)
        self._assoc = universe.get_globals_association(global_name)

    def execute(self, frame):
        if self._is_cached_domain(frame):
            return self._assoc.get_value()
        else:
            return self._next_in_cache.execute(frame)


class _GenericEnforced(AbstractUninitializedGlobalReadNode):

    def execute(self, frame):
        return read_global(self._global_name, frame.get_self(), self._universe,
                           frame.get_executing_domain())
