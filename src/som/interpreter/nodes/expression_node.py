from som.interpreter.nodes.som_node import SOMNode


class ExpressionNode(SOMNode):

    def __init__(self, executes_enforced, source_section = None):
        SOMNode.__init__(self, executes_enforced, source_section)

    def is_super_node(self):
        return False
