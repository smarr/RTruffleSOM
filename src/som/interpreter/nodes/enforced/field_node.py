from rtruffle.node import Node
from som.interpreter.nodes.field_node import AbstractFieldNode, \
    AbstractFieldWriteNode
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.domain import read_field_of, write_to_field_of


_POLYMORPHISM_LIMIT = 6


class _AbstractEnforcedRead(Node):

    def __init__(self):
        Node.__init__(self)


class UninitializedEnforcedRead(_AbstractEnforcedRead):

    _immutable_fields_ = ['_field_idx', '_universe']

    def __init__(self, field_idx, universe):
        _AbstractEnforcedRead.__init__(self)
        self._field_idx = field_idx
        self._universe  = universe

    def _chain_depth(self):
        depth = 0
        current = self
        while isinstance(current, _AbstractEnforcedRead):
            depth += 1
            current = current.get_parent()
        return depth

    def read_field(self, obj, executing_domain):
        assert isinstance(obj, AbstractObject)
        return self._specialize(obj).read_field(obj, executing_domain)

    def read_field_void(self, obj, executing_domain):
        assert isinstance(obj, AbstractObject)
        self._specialize(obj).read_field_void(obj, executing_domain)

    def _specialize(self, obj):
        if self._chain_depth() == _POLYMORPHISM_LIMIT:
            return self.replace(_GenericEnforcedRead(self._field_idx,
                                                     self._universe))

        uninitialized = UninitializedEnforcedRead(self._field_idx,
                                                  self._universe)
        rcvr_domain = obj.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(self._universe)
        return self.replace(_CachedDomainRead(self._field_idx,
                                              rcvr_domain_class,
                                              uninitialized,
                                              self._universe))


class EnforcedFieldReadNode(AbstractFieldNode):

    _immutable_fields_ = ["_read?"]
    _child_nodes_      = ["_read"]

    def __init__(self, self_exp, field_idx, universe, source_section = None):
        AbstractFieldNode.__init__(self, self_exp, True, source_section)
        self._read = self.adopt_child(UninitializedEnforcedRead(field_idx,
                                                                universe))

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        return self._read.read_field(self_obj, frame.get_executing_domain())

    def execute_void(self, frame):
        self_obj = self._self_exp.execute(frame)
        self._read.read_field_void(self_obj, frame.get_executing_domain())


class _CachedDomainRead(_AbstractEnforcedRead):

    _immutable_fields_ = ['_field_idx', '_rcvr_domain_class', '_next_in_cache?',
                          '_universe', '_intercession_handler']
    _child_nodes_      = ['_next_in_cache']

    def __init__(self, field_idx, domain_class, next_in_cache, universe):
        _AbstractEnforcedRead.__init__(self)
        self._field_idx         = universe.new_integer(field_idx + 1)
        self._rcvr_domain_class = domain_class
        self._next_in_cache     = next_in_cache
        self._universe          = universe

        selector = universe.symbol_for("readField:of:")
        self._intercession_handler = domain_class.lookup_invokable(selector)

    def _is_cached_domain(self, rcvr):
        rcvr_domain = rcvr.get_domain(self._universe)
        rcvr_domain_class = rcvr_domain.get_class(self._universe)
        return rcvr_domain_class is self._rcvr_domain_class

    def read_field(self, obj, executing_domain):
        if self._is_cached_domain(obj):
            rcvr_domain = obj.get_domain(self._universe)
            return self._intercession_handler.invoke_unenforced(
                rcvr_domain, [self._field_idx, obj], executing_domain)
        else:
            return self._next_in_cache.read_field(obj, executing_domain)

    def read_field_void(self, obj, executing_domain):
        if self._is_cached_domain(obj):
            rcvr_domain = obj.get_domain(self._universe)
            self._intercession_handler.invoke_unenforced_void(
                rcvr_domain, [self._field_idx, obj], executing_domain)
        else:
            self._next_in_cache.read_field_void(obj, executing_domain)


class _GenericEnforcedRead(_AbstractEnforcedRead):

    _immutable_fields_ = ["_field_idx", "_universe"]

    ## TODO: consider using the field name instead of the index, to make it nicer...

    def __init__(self, field_idx, universe):
        _AbstractEnforcedRead.__init__(self)
        self._field_idx = field_idx ## TODO: should probably convert it already into an SOM Integer
        self._universe  = universe

    def read_field(self, obj, executing_domain):
        return read_field_of(self._field_idx, obj, self._universe,
                             executing_domain)

    def read_field_void(self, obj, execution_domain):
        self.read_field(obj, execution_domain)


class EnforcedFieldWriteNode(AbstractFieldWriteNode):

    _immutable_fields_ = ["_field_idx", "_universe"]

    ## TODO: consider using the field name instead of the index, to make it nicer...

    def __init__(self, self_exp, field_idx, value_exp, universe, source_section = None):
        AbstractFieldWriteNode.__init__(self, self_exp, value_exp, True, source_section)
        self._field_idx = field_idx ## TODO: should probably convert it already into an SOM Integer
        self._universe  = universe

    def write(self, frame, self_obj, value):
        return write_to_field_of(value, self._field_idx, self_obj,
                                 self._universe, frame.get_executing_domain())