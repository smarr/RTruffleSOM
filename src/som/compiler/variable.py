from som.interpreter.nodes.variable_read_node import UninitializedReadNode, \
    UninitializedWriteNode, NonLocalArgumentReadNode, \
    NonLocalTempReadNode, NonLocalTempWriteNode, NonLocalSuperReadNode, \
    NonLocalSelfReadNode, UninitializedArgumentReadNode


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
        if self._name == "self":
            return NonLocalSelfReadNode(context_level, None)
        else:
            return UninitializedArgumentReadNode(self, context_level, None)

    def get_initialized_read_node(self, context_level, source_section):
        assert self._arg_idx >= 0
        return NonLocalArgumentReadNode(context_level, self._arg_idx,
                                        source_section)

    def get_argument_index(self):
        return self._arg_idx

    def get_super_read_node(self, context_level, holder_class_name,
                            on_class_side, universe):
        return NonLocalSuperReadNode(context_level, holder_class_name,
                                     on_class_side, universe)

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
        return NonLocalTempReadNode(context_level, self. _declaration_idx,
                                    source_section)

    def get_write_node(self, context_level, value_expr):
        return UninitializedWriteNode(self, context_level, value_expr, None)

    def get_initialized_write_node(self, context_level, value_expr,
                                   source_section):
        return NonLocalTempWriteNode(context_level, self. _declaration_idx,
                                     value_expr,
                                     source_section)
