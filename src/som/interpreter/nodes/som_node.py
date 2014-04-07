from rtruffle.node import Node


class SOMNode(Node):

    _immutable_fields_ = ['_executes_enforced']

    def __init__(self, enforced, source_section):
        Node.__init__(self, source_section)
        self._executes_enforced = enforced

    def executes_enforced(self):
        return self._executes_enforced
