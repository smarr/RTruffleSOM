from som.interpreter.nodes.variable_read_node import UninitializedReadNode, \
    UninitializedWriteNode, LocalWriteNode, \
    NonLocalArgumentReadNode, LocalSuperReadNode, \
    NonLocalTempReadNode, NonLocalTempWriteNode, NonLocalSuperReadNode, \
    LocalArgumentReadNode, LocalSelfReadNode, NonLocalSelfReadNode, \
    UninitializedArgumentReadNode, LocalTempReadNode


class _Variable(object):

    def __init__(self, name):
        self._name      = name


class Argument(_Variable):

    _immutable_fields_ = ['_arg_idx']

    def __init__(self, name, idx):
        _Variable.__init__(self, name)
        assert name == "self" or name == "$blockSelf" or idx >= 0
        self._arg_idx = idx

    def get_read_node(self, context_level):
        if context_level > 0:
            if self._name == "self":
                return NonLocalSelfReadNode(context_level, None)
            else:
                return UninitializedArgumentReadNode(self, context_level, None)
        else:
            if self._name == "self":
                return LocalSelfReadNode(None)
            else:
                return LocalArgumentReadNode(self._arg_idx, None)

    def get_initialized_read_node(self, context_level, source_section):
        assert context_level > 0
        return NonLocalArgumentReadNode(context_level, self._arg_idx,
                                        source_section)

    def get_argument_index(self):
        return self._arg_idx

    def get_super_read_node(self, context_level, holder_class_name,
                            on_class_side, universe):
        if context_level > 0:
            return NonLocalSuperReadNode(context_level, holder_class_name,
                                         on_class_side, universe)
        else:
            return LocalSuperReadNode(holder_class_name, on_class_side,
                                      universe, None)

    def is_self(self):
        return self._name == "self"


class Local(_Variable):

    _immutable_fields_ = ['_declaration_idx']

    def __init__(self, name, idx):
        _Variable.__init__(self, name)
        assert idx >= 0
        self._declaration_idx = idx

    def get_read_node(self, context_level):
        return UninitializedReadNode(self, context_level, None)

    def get_initialized_read_node(self, context_level, source_section):
        if context_level > 0:
            return NonLocalTempReadNode(context_level, self._declaration_idx,
                                        source_section)
        else:
            return LocalTempReadNode(self._declaration_idx, source_section)

    def get_write_node(self, context_level, value_expr):
        return UninitializedWriteNode(self, context_level, value_expr, None)

    def get_initialized_write_node(self, context_level, value_expr,
                                   source_section):
        assert self._declaration_idx >= 0
        if context_level > 0:
            return NonLocalTempWriteNode(context_level, self._declaration_idx,
                                         value_expr, source_section)
        else:
            return LocalWriteNode(self._declaration_idx, value_expr, source_section)
