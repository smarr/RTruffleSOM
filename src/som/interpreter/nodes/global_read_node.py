from .expression_node import ExpressionNode
from som.vmobjects.domain import read_global


class AbstractUninitializedGlobalReadNode(ExpressionNode):

    _immutable_fields_ = ["_global_name", "_universe"]

    def __init__(self, global_name, universe, executes_enforced, source_section = None):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._global_name = global_name
        self._universe    = universe

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free


class UninitializedGlobalReadNodeEnforced(AbstractUninitializedGlobalReadNode):

    def __init__(self, global_name, universe, source_section = None):
        AbstractUninitializedGlobalReadNode.__init__(self, global_name,
                                                     universe, True,
                                                     source_section)

    def execute(self, frame):
        ## TODO: add optimizations...
        return read_global(frame.get_executing_domain(), self._global_name,
                           self._universe)

    def execute_void(self, frame):
        self.execute(frame)


class UninitializedGlobalReadNodeUnenforced(AbstractUninitializedGlobalReadNode):

    def __init__(self, global_name, universe, source_section = None):
        AbstractUninitializedGlobalReadNode.__init__(self, global_name,
                                                     universe, False,
                                                     source_section)

    def execute(self, frame):
        if self._universe.has_global(self._global_name):
            return self._specialize().execute(frame)
        else:
            return frame.get_self().send_unknown_global_unenforced(
                self._global_name, self._universe, frame.get_executing_domain())

    def _specialize(self):
        assoc = self._universe.get_globals_association(self._global_name)
        cached = CachedGlobalReadNode(assoc, self.get_source_section())
        return self.replace(cached)


class CachedGlobalReadNode(ExpressionNode):

    _immutable_fields_ = ['_assoc']

    def __init__(self, assoc, source_section):
        ExpressionNode.__init__(self, False, source_section)
        self._assoc = assoc

    def execute(self, frame):
        return self._assoc.get_value()

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free
