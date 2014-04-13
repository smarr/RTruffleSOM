from rpython.rlib import jit
from rpython.rlib.debug import make_sure_not_resized
from rtruffle.node import Node

from .frame import Frame


def get_printable_location(invokable):
    return invokable._source_section._identifier

jitdriver = jit.JitDriver(
     greens=['self'],
     virtualizables=['frame'],
     get_printable_location=get_printable_location,
     reds= ['do_void', 'arguments', 'receiver', 'frame'],

     # the next line is a workaround around a likely bug in RPython
     # for some reason, the inlining heuristics default to "never inline" when
     # two different jit drivers are involved (in our case, the primitive
     # driver, and this one).

     # the next line says that calls involving this jitdriver should always be
     # inlined once (which means that things like Integer>>< will be inlined
     # into a while loop again, when enabling this driver).
     should_unroll_one_iteration = lambda self: True)


class Invokable(Node):

    _immutable_fields_ = ['_expr_or_sequence?', '_universe', '_number_of_temps']
    _child_nodes_      = ['_expr_or_sequence']

    def __init__(self, source_section, expr_or_sequence, number_of_temps,
                 universe):
        Node.__init__(self, source_section)
        self._expr_or_sequence = self.adopt_child(expr_or_sequence)
        self._universe         = universe
        self._number_of_temps  = number_of_temps

    def invoke(self, receiver, arguments):
        return self._do_invoke(receiver, arguments, False)

    def invoke_void(self, receiver, arguments):
        self._do_invoke(receiver, arguments, True)

    def _do_invoke(self, receiver, arguments, do_void):
        make_sure_not_resized(arguments)
        frame = Frame(receiver, arguments, self._number_of_temps,
                      self._universe.nilObject)

        jitdriver.jit_merge_point(self=self, receiver=receiver, arguments=arguments, do_void=do_void, frame=frame)


        if do_void:
            self._expr_or_sequence.execute_void(frame)
        else:
            return self._expr_or_sequence.execute(frame)
