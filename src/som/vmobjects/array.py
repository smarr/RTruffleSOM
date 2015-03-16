from rpython.rlib import rerased
from rpython.rlib.objectmodel import instantiate
from .abstract_object import AbstractObject
from rpython.rlib.debug import make_sure_not_resized
from som.vm.globals import nilObject, falseObject, trueObject
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer


class _ArrayStrategy(object):
    pass


class _ObjectStrategy(_ArrayStrategy):

    _erase, _unerase = rerased.new_erasing_pair("obj_list")
    _erase   = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def get_idx(self, storage, idx):
        store = self._unerase(storage)
        return store[idx]

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        store = self._unerase(array._storage)
        store[idx] = value

    def as_arguments_array(self, storage):
        return self._unerase(storage)

    def get_size(self, storage):
        return len(self._unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _ObjectStrategy._erase([nilObject] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        return _ObjectStrategy._erase(values)

    def copy(self, storage):
        store = self._unerase(storage)
        return Array._from_storage_and_strategy(self._erase(store[:]), _obj_strategy)

    def copy_and_extend_with(self, storage, value):
        store = self._unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [None] * new_size

        for i, _ in enumerate(store):
            new[i] = store[i]

        new[old_size]  = value

        return Array._from_storage_and_strategy(self._erase(new), _obj_strategy)


class _LongStrategy(_ArrayStrategy):

    _erase, _unerase = rerased.new_erasing_pair("int_list")
    _erase   = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def get_idx(self, storage, idx):
        store = self._unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], int)
        return Integer(store[idx])

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert isinstance(value, Integer)
        store = self._unerase(array._storage)
        store[idx] = value.get_embedded_integer()

    def as_arguments_array(self, storage):
        store = self._unerase(storage)
        return [Integer(v) for v in store]

    def get_size(self, storage):
        return len(self._unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _LongStrategy._erase([0] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v.get_embedded_integer() for v in values]
        return _LongStrategy._erase(new)

    def copy(self, storage):
        store = self._unerase(storage)
        return Array._from_storage_and_strategy(self._erase(store[:]), _long_strategy)

    def copy_and_extend_with(self, storage, value):
        assert isinstance(value, Integer)
        store = self._unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [0] * new_size

        for i, v in enumerate(store):
            new[i] = v

        new[old_size]  = value.get_embedded_integer()

        return Array._from_storage_and_strategy(self._erase(new), _long_strategy)


class _DoubleStrategy(_ArrayStrategy):

    _erase, _unerase = rerased.new_erasing_pair("double_list")
    _erase   = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def get_idx(self, storage, idx):
        store = self._unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], float)
        return Double(store[idx])

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert isinstance(value, Double)
        store = self._unerase(array._storage)
        store[idx] = value.get_embedded_double()

    def as_arguments_array(self, storage):
        store = self._unerase(storage)
        return [Double(v) for v in store]

    def get_size(self, storage):
        return len(self._unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _DoubleStrategy._erase([0] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v.get_embedded_double() for v in values]
        return _DoubleStrategy._erase(new)

    def copy(self, storage):
        store = self._unerase(storage)
        return Array._from_storage_and_strategy(self._erase(store[:]),
                                                _double_strategy)

    def copy_and_extend_with(self, storage, value):
        assert isinstance(value, Double)
        store = self._unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [0.0] * new_size

        for i, v in enumerate(store):
            new[i] = v

        new[old_size]  = value.get_embedded_double()

        return Array._from_storage_and_strategy(self._erase(new),
                                                _double_strategy)


class _BoolStrategy(_ArrayStrategy):

    _erase, _unerase = rerased.new_erasing_pair("bool_list")
    _erase   = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def get_idx(self, storage, idx):
        store = self._unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], bool)
        return trueObject if store[idx] else falseObject

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert value is trueObject or value is falseObject
        store = self._unerase(array._storage)
        store[idx] = value is trueObject

    def as_arguments_array(self, storage):
        store = self._unerase(storage)
        return [trueObject if v else falseObject for v in store]

    def get_size(self, storage):
        return len(self._unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _BoolStrategy._erase([False] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v is trueObject for v in values]
        return _BoolStrategy._erase(new)

    def copy(self, storage):
        store = self._unerase(storage)
        return Array._from_storage_and_strategy(self._erase(store[:]),
                                                _bool_strategy)

    def copy_and_extend_with(self, storage, value):
        assert value is trueObject or value is falseObject
        store = self._unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [False] * new_size

        for i, v in enumerate(store):
            new[i] = v

        new[old_size]  = value is trueObject

        return Array._from_storage_and_strategy(self._erase(new),
                                                _bool_strategy)


class _EmptyStrategy(_ArrayStrategy):

    # We have these basic erase/unerase methods, and then the once to be used, which
    # do also the wrapping with Integer objects of the integer value
    __erase, __unerase = rerased.new_erasing_pair("Integer")
    __erase   = staticmethod(__erase)
    __unerase = staticmethod(__unerase)

    def _erase(self, anInt):
        assert isinstance(anInt, int)
        return self.__erase(Integer(anInt))

    def _unerase(self, storage):
        return self.__unerase(storage).get_embedded_integer()

    def get_idx(self, storage, idx):
        size = self._unerase(storage)
        if 0 <= idx < size:
            return nilObject
        else:
            raise IndexError()

    def set_idx(self, array, idx, value):
        size = self._unerase(array._storage)
        if 0 <= idx < size:
            if value is nilObject:
                return  # everything is nil already, avoids transition...

            assert isinstance(value, AbstractObject)
            # We need to transition to the _PartiallyEmpty strategy, because
            # we are not guaranteed to set all elements of the array.

            array._storage  = _partially_empty_strategy.new_storage_with_values([nilObject] * size)
            array._strategy = _partially_empty_strategy
            array._strategy.set_idx(array, idx, value)
        else:
            raise IndexError()

    def as_arguments_array(self, storage):
        size = self._unerase(storage)
        return [nilObject] * size

    def get_size(self, storage):
        size = self._unerase(storage)
        return size

    @staticmethod
    def new_storage_for(size):
        return _empty_strategy._erase(size)

    @staticmethod
    def new_storage_with_values(values):
        return _empty_strategy._erase(len(values))

    def copy(self, storage):
        return Array._from_storage_and_strategy(storage, _empty_strategy)

    def copy_and_extend_with(self, storage, value):
        size = self._unerase(storage)
        if value is nilObject:
            return Array.from_size(size + 1)
        else:
            new = [nilObject] * (size + 1)
            new[-1] = value
            return Array._from_storage_and_strategy(_ObjectStrategy._erase(new),
                                                    _obj_strategy)


class _PartialStorage(object):

    _immutable_fields_ = ['storage', 'size']

    @staticmethod
    def from_obj_values(storage):
        # Currently, we support only the direct transition from empty
        # to partially empty
        assert isinstance(storage,    list)
        assert isinstance(storage[0], AbstractObject)
        self = instantiate(_PartiallyEmptyStrategy)
        self.storage        = storage
        self.size           = len(storage)
        self.empty_elements = self.size
        self.type           = None
        return self

    @staticmethod
    def from_size(size):
        self = instantiate(_PartiallyEmptyStrategy)
        self.storage = [nilObject] * size
        self.size    = size
        self.empty_elements = size
        self.type    = None
        return self


class _PartiallyEmptyStrategy(_ArrayStrategy):
    # This is an array that we expect to be slowly filled, and we have the hope
    # that it will turn out to be homogeneous
    # Thus, we track the number of empty slots left, and we track whether it
    # is homogeneous in one type

    _erase, _unerase = rerased.new_erasing_pair("partial_storage")
    _erase   = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def get_idx(self, storage, idx):
        store = self._unerase(storage)
        return store.storage[idx]

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert isinstance(value, AbstractObject)
        store = self._unerase(array._storage)

        if value is nilObject:
            if store.storage[idx] is nilObject:
                return
            else:
                store.storage[idx] = nilObject
                store.empty_elements += 1
                return
        if store.storage[idx] is nilObject:
            store.empty_elements -= 1

        store.storage[idx] = value

        if isinstance(value, Integer):
            if store.type is None:
                store.type = _long_strategy
            elif store.type is not _long_strategy:
                store.type = _obj_strategy
        elif isinstance(value, Double):
            if store.type is None:
                store.type = _double_strategy
            elif store.type is not _double_strategy:
                store.type = _obj_strategy
        elif value is trueObject or value is falseObject:
            if store.type is None:
                store.type = _bool_strategy
            elif store.type is not _bool_strategy:
                store.type = _obj_strategy
        else:
            store.type = _obj_strategy

        if store.empty_elements == 0:
            array._strategy = store.type
            array._storage = array._strategy.new_storage_with_values(store.storage)

    def as_arguments_array(self, storage):
        return self._unerase(storage).storage

    def get_size(self, storage):
        return self._unerase(storage).size

    @staticmethod
    def new_storage_for(size):
        return _PartiallyEmptyStrategy._erase(
            _PartiallyEmptyStrategy.from_size(size))

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        return _PartiallyEmptyStrategy._erase(
            _PartialStorage.from_obj_values(values))

    def copy(self, storage):
        store = self._unerase(storage)
        return Array._from_storage_and_strategy(
            self._erase(_PartialStorage.from_obj_values(store.storage[:])),
            _partially_empty_strategy)

    def copy_and_extend_with(self, storage, value):
        store = self._unerase(storage)
        old_size = store.size
        new_size = old_size + 1

        new = [nilObject] * new_size

        for i, _ in enumerate(store.storage):
            new[i] = store.storage[i]

        new_store = instantiate(_PartiallyEmptyStrategy)
        new_store.storage        = new
        new_store.size           = new_size
        new_store.empty_elements = store.empty_elements + 1
        new_store.type           = store.type

        new_arr = Array._from_storage_and_strategy(self._erase(new_store),
                                                   _partially_empty_strategy)
        new_arr.set_indexable_field(old_size, value)
        return new_arr


_obj_strategy    = _ObjectStrategy()
_long_strategy   = _LongStrategy()
_double_strategy = _DoubleStrategy()
_bool_strategy   = _BoolStrategy()
_empty_strategy  = _EmptyStrategy()
_partially_empty_strategy = _PartiallyEmptyStrategy()


class Array(AbstractObject):

    # _strategy is the strategy object
    # _storage depends on the strategy, can be for instance a typed list,
    # or for the empty strategy the size as an Integer object,
    # or something more complex

    @staticmethod
    def _from_storage_and_strategy(storage, strategy):
        self = instantiate(Array)
        # self = Array()
        self._strategy = strategy
        self._storage  = storage
        return self

    @staticmethod
    def from_size(size, strategy = _empty_strategy):
        self = instantiate(Array)
        # self = Array()
        self._strategy = strategy
        self._storage  = strategy.new_storage_for(size)
        return self

    @staticmethod
    def from_values(values, strategy = None):
        self = instantiate(Array)
        # self = Array()
        if strategy is None:
            self._strategy = self._determine_strategy(values)
        else:
            self._strategy = strategy
        self._storage = self._strategy.new_storage_with_values(values)
        return self

    @staticmethod
    def from_integers(ints):
        return Array._from_storage_and_strategy(_long_strategy._erase(ints),
                                                _long_strategy)

    @staticmethod
    def from_objects(values):
        return Array.from_values(values, _obj_strategy)

    @staticmethod
    def _determine_strategy(values):
        is_empty    = True
        only_double = True
        only_long   = True
        only_bool   = True
        for v in values:
            if v is None or v is nilObject:
                continue
            if isinstance(v, int) or isinstance(v, Integer):
                only_double = False
                is_empty    = False
                continue
            if isinstance(v, float) or isinstance(v, Double):
                only_long = False
                is_empty  = False
                continue
            if isinstance(v, bool) or v is trueObject or v is falseObject:
                only_bool = False
                is_empty  = False
                continue
            only_long   = False
            only_double = False
            only_bool   = False
            is_empty    = False

        if is_empty:
            return _empty_strategy
        if only_double:
            return _double_strategy
        if only_long:
            return _long_strategy
        if only_bool:
            return _bool_strategy
        return _obj_strategy

    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        return self._strategy.get_idx(self._storage, index)

    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        self._strategy.set_idx(self, index, value)

    def as_argument_array(self):
        return self._strategy.as_arguments_array(self._storage)

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return self._strategy.get_size(self._storage)

    def copy(self):
        return self._strategy.copy(self._storage)

    def copy_and_extend_with(self, value):
        return self._strategy.copy_and_extend_with(self._storage, value)

    def get_class(self, universe):
        return universe.arrayClass
