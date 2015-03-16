from .contextual_node import ContextualNode
from .expression_node import ExpressionNode

from rpython.rlib import jit
from som.vmobjects.block import Block


class UninitializedReadNode(ExpressionNode):

    _immutable_fields_ = ['_var', '_context_level']

    def __init__(self, var, context_level, source_section):
        ExpressionNode.__init__(self, source_section)
        self._var           = var
        self._context_level = context_level

    def execute(self, frame):
        return self._specialize().execute(frame)

    def _specialize(self):
        return self.replace(self._var.get_initialized_read_node(
            self._context_level, self._source_section))


class UninitializedArgumentReadNode(UninitializedReadNode):

    def _specialize(self):
        return self.replace(self._var.get_initialized_read_node(
            self._context_level, self._source_section))


class UninitializedWriteNode(ExpressionNode):

    _immutable_fields_ = ['_var', '_context_level', '_value_expr']

    def __init__(self, var, context_level, value_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._var           = var
        self._context_level = context_level
        self._value_expr    = value_expr

    def execute(self, frame):
        return self._specialize().execute(frame)

    def _specialize(self):
        return self.replace(self._var.get_initialized_write_node(
            self._context_level, self._value_expr, self._source_section))


class _NonLocalVariableNode(ContextualNode):

    _immutable_fields_ = ["_frame_idx"]

    def __init__(self, context_level, frame_idx, source_section):
        ContextualNode.__init__(self, context_level, source_section)
        assert frame_idx >= 0
        self._frame_idx = frame_idx


class _NonLocalVariableReadNode(_NonLocalVariableNode):

    def execute(self, frame):
        if self._context_level == 0:
            return self._do_local_var_read(frame)
        block = self.determine_block(frame)
        return self._do_nonlocal_var_read(block)


class NonLocalArgumentReadNode(_NonLocalVariableReadNode):

    def _do_local_var_read(self, frame):
        return frame.get_argument(self._frame_idx)

    def _do_nonlocal_var_read(self, block):
        assert isinstance(block, Block)
        return block.get_context_argument(self._frame_idx)


class NonLocalTempReadNode(_NonLocalVariableReadNode):

    def _do_local_var_read(self, frame):
        return frame.get_temp(self._frame_idx)

    def _do_nonlocal_var_read(self, block):
        assert isinstance(block, Block)
        return block.get_context_temp(self._frame_idx)


class NonLocalSelfReadNode(ContextualNode):

    def __init__(self, context_level, source_section):
        ContextualNode.__init__(self, context_level, source_section)

    def execute(self, frame):
        if self._context_level == 0:
            return frame.get_self()
        return self.determine_outer_self(frame)


class NonLocalSuperReadNode(NonLocalSelfReadNode):

    _immutable_fields_ = ["_super_class_name", "_on_class_side", "_universe"]

    def __init__(self, context_level, super_class_name, on_class_side,
                 universe, source_section = None):
        NonLocalSelfReadNode.__init__(self, context_level, source_section)
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


class NonLocalTempWriteNode(_NonLocalVariableNode):

    _immutable_fields_ = ['_value_expr?']
    _child_nodes_      = ['_value_expr']

    def __init__(self, context_level, frame_idx, value_expr,
                 source_section = None):
        _NonLocalVariableNode.__init__(self, context_level, frame_idx,
                                       source_section)
        self._value_expr = self.adopt_child(value_expr)

    def execute(self, frame):
        value = self._value_expr.execute(frame)
        if self._context_level == 0:
            frame.set_temp(self._frame_idx, value)
        else:
            self.determine_block(frame).set_context_temp(self._frame_idx, value)
        return value
