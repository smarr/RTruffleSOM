from som.vm.globals import nilObject


class _FrameOnStackMarker(object):

    def __init__(self):
        self._on_stack = True

    def mark_as_no_longer_on_stack(self):
        self._on_stack = False

    def is_on_stack(self):
        return self._on_stack

_EMPTY_LIST = []


class Frame(object):
        
    _immutable_fields_ = ['_receiver', '_arguments[*]', '_temps', '_on_stack']

    def __init__(self, receiver, arguments, num_temps):
        self._receiver        = receiver
        self._arguments       = arguments
        self._on_stack        = _FrameOnStackMarker()
        self._temps           = [nilObject] * num_temps

    def get_context_values(self):
        return self._receiver, self._arguments, self._temps, self._on_stack

    def get_argument(self, index):
        return self._arguments[index]

    def set_argument(self, index, value):
        self._arguments[index] = value

    def get_temp(self, index):
        temps = self._temps
        assert 0 <= index < len(temps)
        assert temps is not None
        return temps[index]

    def set_temp(self, index, value):
        temps = self._temps
        assert temps is not None
        assert 0 <= index < len(temps)
        temps[index] = value

    def get_self(self):
        return self._receiver

    def get_on_stack_marker(self):
        return self._on_stack

    def __str__(self):
        return "Frame(%s, %s, %s)" % (self._receiver, self._arguments,
                                      self._temps)
