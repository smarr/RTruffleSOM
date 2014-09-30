from ..expression_node import ExpressionNode


class BinaryExpressionNode(ExpressionNode):

    _immutable_fields_ = ['_rcvr_node?', '_arg_node?']
    _child_nodes_      = ['_rcvr_node',  '_arg_node']

    def __init__(self, rcvr_node, arg_node, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_node = self.adopt_child(rcvr_node)
        self._arg_node  = self.adopt_child(arg_node)

    def execute(self, frame):
        rcvr = self._rcvr_node.execute(frame)
        arg  = self._arg_node.execute(frame)
        return self.execute_binary_evaluated(frame, rcvr, arg)

    def execute_void(self, frame):
        rcvr = self._rcvr_node.execute(frame)
        arg  = self._arg_node.execute(frame)
        self.execute_binary_evaluated_void(frame, rcvr, arg)


class BinarySideEffectFreeExpressionNode(BinaryExpressionNode):

    def execute_binary_evaluated_void(self, frame, rcvr, arg):
        pass  # NOOP, side effect free
