from rpython.rlib import jit
from rpython.rlib.debug import make_sure_not_resized

from .frame import Frame
from rtruffle.node import Node


def get_printable_location(invokable, executing_domain):
    return invokable._source_section._identifier

jitdriver = jit.JitDriver(
     greens=['self', 'executing_domain'],
     # virtualizables=['caller_frame'])
      get_printable_location=get_printable_location,
     reds= ['do_void', 'enforced', 'arguments', 'receiver'], #, 'frame'

     # the next line is a workaround around a likely bug in RPython
     # for some reason, the inlining heuristics default to "never inline" when
     # two different jit drivers are involved (in our case, the primitive
     # driver, and this one).

     # the next line says that calls involving this jitdriver should always be
     # inlined once (which means that things like Integer>>< will be inlined
     # into a while loop again, when enabling this driver).
     should_unroll_one_iteration = lambda self, executing_domain: True)


class Invokable(Node):

    _immutable_fields_ = ['_body_enforced?', '_body_unenforced?',
                          '_universe', '_number_of_temps']
    _child_nodes_      = ['_body_enforced', '_body_unenforced']

    def __init__(self, source_section, body_enforced, body_unenforced,
                 number_of_temps, universe):
        Node.__init__(self, source_section)
        self._body_enforced    = self.adopt_child(body_enforced)
        self._body_unenforced  = self.adopt_child(body_unenforced)
        self._universe         = universe
        self._number_of_temps  = number_of_temps

    def invoke_enforced(self, receiver, arguments, executing_domain):
        return self._do_invoke(receiver, arguments, executing_domain,
                               False, True)

    def invoke_enforced_void(self, receiver, arguments, executing_domain):
        self._do_invoke(receiver, arguments, executing_domain, True, True)

    def invoke_unenforced(self, receiver, arguments, executing_domain):
        return self._do_invoke(receiver, arguments, executing_domain,
                               False, False)

    def invoke_unenforced_void(self, receiver, arguments, executing_domain):
        self._do_invoke(receiver, arguments, executing_domain, True, False)

    def _do_invoke(self, receiver, arguments, executing_domain,
                   do_void, enforced):
        assert arguments is not None
        make_sure_not_resized(arguments)

        jitdriver.jit_merge_point(self=self, receiver=receiver, # frame=frame,
                                  arguments=arguments, executing_domain=executing_domain,
                                  enforced=enforced, do_void=do_void)
        frame = Frame(receiver, arguments, self._number_of_temps,
                      self._universe.nilObject, executing_domain)
        if enforced:
            if do_void:
                self._body_enforced.execute_void(frame)
                return
            else:
                return self._body_enforced.execute(frame)
        else:
            if do_void:
                self._body_unenforced.execute_void(frame)
                return
            else:
                return self._body_unenforced.execute(frame)


class InvokableUnenforced(Invokable):

    def __init__(self, source_section, body_unenforced,
                 number_of_temps, universe):
        Invokable.__init__(self, source_section, body_unenforced,
                           body_unenforced, number_of_temps, universe)

    def invoke_enforced(self, receiver, arguments, domain):
        return self._do_invoke(receiver, arguments, domain, False, False)

    def invoke_enforced_void(self, receiver, arguments, domain):
        self._do_invoke(receiver, arguments, domain, True, False)
