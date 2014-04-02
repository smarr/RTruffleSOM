from .contextual_node import ContextualNode

from rpython.rlib import jit


class NonLocalVariableNode(ContextualNode):

    _immutable_fields_ = ["_is_argument", "_frame_idx"]

    def __init__(self, context_level, frame_idx, is_argument,
                 executes_enforced, source_section):
        ContextualNode.__init__(self, context_level, executes_enforced,
                                source_section)
        self._is_argument   = is_argument
        self._frame_idx     = frame_idx


class NonLocalVariableReadNode(NonLocalVariableNode):

    def __init__(self, context_level, frame_idx, is_argument,
                 executes_enforced, source_section):
        NonLocalVariableNode.__init__(self, context_level, frame_idx,
                                      is_argument, executes_enforced,
                                      source_section)

    def execute(self, frame):
        ctx = self.determine_context(frame)
        if self._is_argument:
            return ctx.get_argument(self._frame_idx)
        else:
            return ctx.get_temp(self._frame_idx)

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free


class NonLocalSelfReadNode(ContextualNode):

    def __init__(self, context_level, executes_enforced, source_section):
        ContextualNode.__init__(self, context_level, executes_enforced,
                                source_section)

    def execute(self, frame):
        ctx = self.determine_context(frame)
        return ctx.get_self()

    def execute_void(self, frame):
        pass  # NOOP, because it is side-effect free


class NonLocalSuperReadNode(NonLocalSelfReadNode):

    _immutable_fields_ = ["_super_class_name", "_on_class_side", "_universe"]

    def __init__(self, context_level, super_class_name, on_class_side,
                 universe, executes_enforced, source_section):
        NonLocalSelfReadNode.__init__(self, context_level, executes_enforced,
                                      source_section)
        self._super_class_name = super_class_name
        self._on_class_side    = on_class_side
        self._universe         = universe

    @jit.elidable_promote('all')
    def _get_lexical_super_class(self):
        clazz = self._universe.get_global(self._super_class_name)
        if self._on_class_side:
            clazz = clazz.get_class(self._universe)
        return clazz.get_super_class()

    def is_super_node(self):
        return True

    def get_super_class(self):
        return self._get_lexical_super_class()


class NonLocalVariableWriteNode(NonLocalVariableNode):

    _immutable_fields_ = ['_value_expr?']
    _child_nodes_      = ['_value_expr']

    def __init__(self, context_level, frame_idx, value_expr,
                 executes_enforced, source_section):
        NonLocalVariableNode.__init__(self, context_level, frame_idx,
                                      False, executes_enforced, source_section)
        self._value_expr = self.adopt_child(value_expr)

    def execute(self, frame):
        value = self._value_expr.execute(frame)
        self.determine_context(frame).set_temp(self._frame_idx, value)
        return value

    def execute_void(self, frame):
        self.execute(frame)
