from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.rbigint import rbigint

from rtruffle.node import UnexpectedResultException

from .arithmetic import ArithmeticPrim
from ...interpreter.nodes.message.generic_node import GenericMessageNode
from ...vmobjects.biginteger import BigInteger
from ...vmobjects.clazz      import Class
from ...vmobjects.double     import Double
from ...vmobjects.integer    import Integer
from ...vmobjects.string     import String
from ...vmobjects.symbol     import Symbol


class AdditionPrim(ArithmeticPrim):

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return selector.get_string() == "+"

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(_UninitializedAdditionPrim(node._rcvr_expr,
                                                       node._arg_exprs[0],
                                                       node._universe,
                                                       node._source_section))

    ## This should be what I need to write:
    # @specialization(rewrite_on = OverflowError)
    def add_int_int_return_int(self, rcvr, arg):
        assert isinstance(rcvr, int)
        assert isinstance(arg,  int)
        return ovfcheck(rcvr + arg)

    # @specialization
    def add_int_int_return_sabstractobject_with_overflow(self, rcvr, arg):
        assert isinstance(rcvr, int)
        assert isinstance(arg,  int)
        result = rbigint.fromint(rcvr).add(rbigint.fromint(arg))
        return self._reduce_to_int_if_possible(result)

    # @specialization
    # We chose to use a wrapped representation, because we want to reduce
    # to integer if possible, and to unify the return type, it is better to
    # choose AbstractObject
    def add_sbiginteger_sbiginteger_return_sabstractobject(self, rcvr, arg):
        result = rcvr.get_embedded_biginteger().add(arg.get_embedded_biginteger())
        return self._reduce_to_int_if_possible(result)

    # @specialization
    def add_float_float_return_float(self, rcvr, arg):
        assert isinstance(rcvr, float)
        assert isinstance(arg,  float)
        return rcvr + arg

    # @specialization
    def add_string_string_return_string(self, rcvr, arg):
        assert isinstance(rcvr, str)
        assert isinstance(arg,  str)
        return rcvr + arg

    # @specialization
    def add_int_sbiginteger_return_sabstractobject(self, rcvr, arg):
        assert isinstance(rcvr, int)
        assert isinstance(arg,  BigInteger)
        result = rbigint.fromint(rcvr).add(arg.get_embedded_biginteger())
        return self._reduce_to_int_if_possible(result)

    # @specialization
    def add_int_float_return_float(self, rcvr, arg):
        assert isinstance(rcvr, int)
        assert isinstance(arg,  float)
        return self.add_float_float_return_float(float(rcvr), arg)

    # @specialization
    def add_sbiginteger_int_return_sabstractobject(self, rcvr, arg):
        assert isinstance(rcvr, BigInteger)
        assert isinstance(arg,  int)
        result = rcvr.get_embedded_biginteger().add(rbigint.fromint(arg))
        return self._reduce_to_int_if_possible(result)

    # @specialization
    def add_float_int_return_float(self, rcvr, arg):
        assert isinstance(rcvr, float)
        assert isinstance(arg,  int)
        return rcvr + float(arg)

    # @specialization
    def add_string_sclass_return_string(self, rcvr, arg):
        assert isinstance(rcvr, str)
        assert isinstance(arg,  Class)
        return rcvr + arg.get_name().get_string()

    # @specialization
    def add_string_ssymbol_return_string(self, rcvr, arg):
        assert isinstance(rcvr, str)
        assert isinstance(arg,  Symbol)
        return rcvr + arg.get_string()

    # @specialization
    # def add_abstract_object_abstract_object_return_abstract_object(
    #         self, frame, rcvr, arg):
    #     if isinstance(rcvr, BigInteger):
    #         return rcvr.prim_add(arg, self._universe)
    #     elif isinstance(rcvr, Double):
    #         return rcvr.prim_add(arg, self._universe)
    #     elif isinstance(rcvr, String):
    #         if  not isinstance(arg, String):
    #             return self.replace(GenericMessageNode(
    #                 self._universe.symbol_for("+"), self._universe,
    #                 self._rcvr_node, [self._arg_node], self._source_section)).\
    #                     execute_evaluated(frame, rcvr, [arg])
    #
    #         return self._universe.new_string(rcvr.get_embedded_string()
    #                                          + arg.get_embedded_string())
    #     else:
    #         raise RuntimeError("Unhandled case? should not happen!")

## ----------------------------------------------------------------------
## Here comes all the stuff that should be generated


class _UninitializedAdditionPrim(AdditionPrim):

    def execute_evaluated(self, frame, rcvr, args):
        assert len(args) == 1
        return self.execute_binary_evaluated(frame, rcvr, args[0])

    def execute_evaluated_void(self, frame, rcvr, args):
        assert len(args) == 1
        self.execute_binary_evaluated_void(frame, rcvr, args[0])

    def execute_binary_evaluated(self, frame, rcvr, arg):
        return self._specialize(rcvr, arg).\
            execute_binary_evaluated(frame, rcvr, arg)

    def execute_binary_evaluated_void(self, frame, rcvr, arg):
        self._specialize(rcvr, arg).\
            execute_binary_evaluated_void(frame, rcvr, arg)

    def _specialize(self, rcvr, arg):
        if isinstance(rcvr, Integer):
            if isinstance(arg, Integer):
                return self.replace(_AdditionIntIntReturnInt(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, BigInteger):
                return self.replace(_AdditionIntSBigIntegerReturnSAbstractObject(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, Double):
                return self.replace(_AdditionIntFloatReturnFloat(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
        if isinstance(rcvr, BigInteger):
            if isinstance(arg, BigInteger):
                return self.replace(_AdditionSBigIntegerSBigIntegerReturnSAbstractObject(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, Integer):
                return self.replace(_AdditionSBigIntegerIntReturnSAbstractObject(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
        if isinstance(rcvr, Double):
            if isinstance(arg, Double):
                return self.replace(_AdditionFloatFloatReturnFloat(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, Integer):
                return self.replace(_AdditionFloatIntReturnFloat(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
        if isinstance(rcvr, String):
            if isinstance(arg, String):
                return self.replace(_AdditionStringStringReturnString(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, Class):
                return self.replace(_AdditionStringSClassReturnString(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))
            if isinstance(arg, Symbol):
                return self.replace(_AdditionStringSSymbolReturnString(
                    self._rcvr_node, self._arg_node, self._universe,
                    self._source_section))

        # No specialization applicable, so, just do a normal message send
        return self.replace(GenericMessageNode(
            self._universe.symbol_for("+"), self._universe, self._rcvr_node,
            [self._arg_node], self._source_section))



## TODO: look into:
## there's also rpython.rlib.objectmodel.specialize
## the "easy way" to generate several copies of a function with the same body
## the same Python body, that is; not the same translated-to-C body

class _AdditionIntIntReturnInt(AdditionPrim):

    def execute(self, frame):
        try:
            result = self.execute_int(frame)
            return self._universe.new_integer(result)
        except UnexpectedResultException as e:
            return e.get_result()

    def execute_int(self, frame):
        rcvr = self._rcvr_node.execute_int(frame)
        arg  = self._arg_node.execute_int(frame)
        try:
            return self.add_int_int_return_int(rcvr, arg)
        except OverflowError:
            result_obj = self._respecialize_on_overflow().\
                execute_binary_evaluated(
                    frame, self._universe.new_integer(rcvr),
                    self._universe.new_integer(arg))
            raise UnexpectedResultException(result_obj)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Integer)
        if isinstance(arg, Double):
            print arg
            r = self._universe.new_double(float(rcvr.get_embedded_integer()))
            return r.prim_add(arg, self._universe)

        if not isinstance(arg, Integer):
            print arg
            raise UnexpectedResultException(arg)

        try:
            return self._universe.new_integer(self.add_int_int_return_int(
                rcvr.get_embedded_integer(), arg.get_embedded_integer()))
        except OverflowError:
            result_obj = self._respecialize_on_overflow().\
                execute_binary_evaluated(frame, rcvr, arg)
            raise UnexpectedResultException(result_obj)

    def _respecialize_on_overflow(self):
        return self.replace(_AdditionIntIntReturnSAbstractObjectWithOverflow(
            self._rcvr_node, self._arg_node, self._universe,
            self._source_section))


class _AdditionIntIntReturnSAbstractObjectWithOverflow(AdditionPrim):
    def execute(self, frame):
        rcvr = self._rcvr_node.execute_int(frame)
        arg  = self._arg_node.execute_int(frame)
        return self.add_int_int_return_sabstractobject_with_overflow(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Integer)
        assert isinstance(arg,  Integer)
        return self.add_int_int_return_sabstractobject_with_overflow(
            rcvr.get_embedded_integer(), arg.get_embedded_integer())


class _AdditionSBigIntegerSBigIntegerReturnSAbstractObject(AdditionPrim):
    def execute(self, frame):
        rcvr = self._rcvr_node.execute(frame)
        arg  = self._arg_node.execute(frame)
        return self.add_sbiginteger_sbiginteger_return_sabstractobject(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, BigInteger)
        assert isinstance(arg,  BigInteger)
        return self.add_sbiginteger_sbiginteger_return_sabstractobject(rcvr, arg)


class _AdditionFloatFloatReturnFloat(AdditionPrim):
    def execute(self, frame):
        result = self.execute_float(frame)
        return self._universe.new_double(result)

    def execute_float(self, frame):
        rcvr = self._rcvr_node.execute_float(frame)
        arg  = self._arg_node.execute_float(frame)
        return self.add_float_float_return_float(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Double)
        assert isinstance(arg,  Double)
        result = self.add_float_float_return_float(rcvr.get_embedded_double(),
                                                   arg.get_embedded_double())
        return self._universe.new_double(result)


class _AdditionStringStringReturnString(AdditionPrim):
    def execute(self, frame):
        result = self.execute_string(frame)
        return self._universe.new_string(result)

    def execute_string(self, frame):
        rcvr = self._rcvr_node.execute_string(frame)
        arg  = self._arg_node.execute_string(frame)
        return self.add_string_string_return_string(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, String)
        assert isinstance(arg,  String)
        result = self.add_string_string_return_string(rcvr.get_embedded_string(),
                                                      arg.get_embedded_string())
        return self._universe.new_string(result)


class _AdditionIntSBigIntegerReturnSAbstractObject(AdditionPrim):

    def execute(self, frame):
        rcvr = self._rcvr_node.execute_int(frame)
        arg  = self._arg_node.execute(frame)
        return self.add_int_sbiginteger_return_sabstractobject(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Integer)
        assert isinstance(arg, BigInteger)
        return self.add_int_sbiginteger_return_sabstractobject(
            rcvr.get_embedded_integer(), arg)


class _AdditionIntFloatReturnFloat(AdditionPrim):

    def execute(self, frame):
        result = self.execute_float(frame)
        return self._universe.new_double(result)

    def execute_float(self, frame):
        rcvr = self._rcvr_node.execute_int(frame)
        arg  = self._arg_node.execute_float(frame)
        return self.add_int_float_return_float(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Integer)
        assert isinstance(arg,  Double)
        result = self.add_int_float_return_float(rcvr.get_embedded_integer(),
                                                 arg.get_embedded_double())
        return self._universe.new_double(result)


class _AdditionSBigIntegerIntReturnSAbstractObject(AdditionPrim):

    def execute(self, frame):
        rcvr = self._rcvr_node.execute(frame)
        arg  = self._arg_node.execute_int(frame)
        return self.add_sbiginteger_int_return_sabstractobject(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, BigInteger)
        assert isinstance(arg,  Integer)
        return self.add_sbiginteger_int_return_sabstractobject(
            rcvr, arg.get_embedded_integer())


class _AdditionFloatIntReturnFloat(AdditionPrim):

    def execute(self, frame):
        result = self.execute_float(frame)
        return self._universe.new_double(result)

    def execute_float(self, frame):
        rcvr = self._rcvr_node.execute_float(frame)
        arg  = self._arg_node.execute_int(frame)
        return self.add_float_int_return_float(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, Double)
        assert isinstance(arg,  Integer)
        result = self.add_float_int_return_float(rcvr.get_embedded_double(),
                                                 arg.get_embedded_integer())
        return self._universe.new_double(result)


class _AdditionStringSClassReturnString(AdditionPrim):
    def execute(self, frame):
        result = self.execute_string(frame)
        return self._universe.new_string(result)

    def execute_string(self, frame):
        rcvr = self._rcvr_node.execute_string(frame)
        arg  = self._arg_node.execute(frame)
        return self.add_string_sclass_return_string(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, String)
        assert isinstance(arg,  Class)
        result = self.add_string_sclass_return_string(rcvr.get_embedded_string(), arg)
        return self._universe.new_string(result)


class _AdditionStringSSymbolReturnString(AdditionPrim):
    def execute(self, frame):
        result = self.execute_string(frame)
        return self._universe.new_string(result)

    def execute_string(self, frame):
        rcvr = self._rcvr_node.execute_string(frame)
        arg  = self._arg_node.execute(frame)
        return self.add_string_ssymbol_return_string(rcvr, arg)

    def execute_binary_evaluated(self, frame, rcvr, arg):
        assert isinstance(rcvr, String)
        assert isinstance(arg,  Symbol)
        result = self.add_string_ssymbol_return_string(rcvr.get_embedded_string(), arg)
        return self._universe.new_string(result)


# class _NonIntCases(AdditionPrim):
#
#     def execute_binary_evaluated(self, frame, rcvr, arg):
#         assert isinstance(rcvr, AbstractObject)
#         assert isinstance(arg,  AbstractObject)
#         return self.process_abstract_object_abstract_object_return_abstract_object(
#             frame, rcvr, arg)
