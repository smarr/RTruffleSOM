from rtruffle.node import Node

from .frame import Frame
from .control_flow import ReturnException


class Invokable(Node):

    _immutable_fields_ = ['_expr_or_sequence?', '_universe', '_arg_mapping[*]',
                          '_num_temps']
    _child_nodes_      = ['_expr_or_sequence']

    def __init__(self, source_section, expr_or_sequence, number_of_temps,
                 universe):
        Node.__init__(self, source_section)
        self._expr_or_sequence  = self.adopt_child(expr_or_sequence)
        self._universe          = universe
        self._num_temps         = number_of_temps

    def invoke(self, receiver, arguments):
        assert arguments is not None
        frame = Frame(receiver, arguments, self._num_temps)

        marker = frame.get_on_stack_marker()
        try:
            return self._expr_or_sequence.execute(frame)
        except ReturnException as e:
            if not e.has_reached_target(marker):
                raise e
            else:
                return e.get_result()
        finally:
            marker.mark_as_no_longer_on_stack()
