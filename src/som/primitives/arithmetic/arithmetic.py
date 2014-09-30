from ...interpreter.nodes.nary.binary import BinarySideEffectFreeExpressionNode


class ArithmeticPrim(BinarySideEffectFreeExpressionNode):

    _immutable_fields_ = ['_universe']

    def __init__(self, rcvr_node, arg_node, universe, source_section):
        BinarySideEffectFreeExpressionNode.__init__(self, rcvr_node, arg_node,
                                                    source_section)
        self._universe = universe

    def _reduce_to_int_if_possible(self, big_int):
        try:
            return self._universe.new_integer(big_int.toint())
        except OverflowError:
            return self._universe.new_biginteger(big_int)
