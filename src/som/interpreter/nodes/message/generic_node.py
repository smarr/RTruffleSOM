from rpython.rlib.debug import make_sure_not_resized
from rpython.rlib.jit import we_are_jitted

from .abstract_node import AbstractMessageNode


class GenericMessageNode(AbstractMessageNode):

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self.execute_evaluated(frame, rcvr, args)

    def execute_evaluated(self, frame, rcvr, args):
        assert frame is not None
        assert rcvr is not None
        assert args is not None
        make_sure_not_resized(args)
        return self._direct_dispatch(rcvr, args)

    def _direct_dispatch(self, rcvr, args):
        method = self._lookup_method(rcvr)
        if method:
            return method.invoke(rcvr, args)
        else:
            return rcvr.send_does_not_understand(self._selector, args,
                                                 self._universe)

    def _lookup_method(self, rcvr):
        rcvr_class = self._class_of_receiver(rcvr)
        return rcvr_class.lookup_invokable(self._selector)

    def _class_of_receiver(self, rcvr):
        if self._rcvr_expr.is_super_node():
            return self._rcvr_expr.get_super_class()
        return rcvr.get_class(self._universe)

    def __str__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               self._selector,
                               self._source_section)
