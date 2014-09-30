from rtruffle.node import Node, UnexpectedResultException
from ...vmobjects.double  import Double
from ...vmobjects.integer import Integer
from ...vmobjects.string  import String


class ExpressionNode(Node):

    def __init__(self, source_section):
        Node.__init__(self, source_section)

    def is_super_node(self):
        return False

    def execute(self, frame):
        raise NotImplementedError("subclass responsibility")

    def execute_void(self, frame):
        raise NotImplementedError("subclass responsibility")

    def execute_int(self, frame):
        result = self.execute(frame)
        if isinstance(result, Integer):
            return result.get_embedded_integer()
        else:
            raise UnexpectedResultException(result)

    def execute_float(self, frame):
        result = self.execute(frame)
        if isinstance(result, Double):
            return result.get_embedded_double()
        else:
            raise UnexpectedResultException(result)

    def execute_string(self, frame):
        result = self.execute(frame)
        if isinstance(result, String):
            return result.get_embedded_string()
        else:
            raise UnexpectedResultException(result)
