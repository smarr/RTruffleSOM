from rpython.rlib import jit
from rpython.rlib.debug import make_sure_not_resized


class Frame(object):
        
    _immutable_fields_ = ["_receiver", "_arguments[*]", "_temps"]
    _virtualizable_    = ["_temps[*]"]

    def __init__(self, receiver, arguments, number_of_temps,
                 nilObject):
        make_sure_not_resized(arguments)
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._receiver       = receiver
        self._arguments      = arguments
        self._on_stack       = True
        self._temps          = [nilObject] * number_of_temps

    def get_argument(self, index):
        jit.promote(index)
        return self._arguments[index]

    def set_argument(self, index, value):
        self._arguments[index] = value

    def get_temp(self, index):
        jit.promote(index)
        temps = self._temps
        assert 0 <= index < len(temps)
        assert temps is not None
        return temps[index]

    def set_temp(self, index, value):
        jit.promote(index)
        temps = self._temps
        assert temps is not None
        assert 0 <= index < len(temps)
        temps[index] = value

    def get_self(self):
        return self._receiver

    def is_on_stack(self):
        return self._on_stack

    def mark_as_no_longer_on_stack(self):
        self._on_stack = False

    def __str__(self):
        return "Frame(%s, %s, %s)" % (self._receiver, self._arguments,
                                      self._temps)
