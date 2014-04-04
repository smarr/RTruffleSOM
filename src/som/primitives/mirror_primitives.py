from som.primitives.primitives import Primitives
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.block import Block
from som.vmobjects.object import Object
from som.vmobjects.primitive import Primitive


def _domain_of(ivkbl, rcvr, args, domain):
    assert isinstance(args[0], AbstractObject)
    return args[0].get_domain(ivkbl.get_universe())


def _set_domain_of_to(ivkbl, rcvr, args, domain):
    assert isinstance(args[0], AbstractObject)
    assert isinstance(args[1], Object)
    args[0].set_domain(args[1])
    return rcvr


def _evaluate_in(ivkbl, rcvr, args, domain):
    assert isinstance(args[0], Block)
    assert isinstance(args[1], Object)
    return args[0].get_method().invoke_unenforced(args[0], None, args[1])


def _evaluated_enforced_in(ivkbl, rcvr, args, domain):
    assert isinstance(args[0], Block)
    assert isinstance(args[1], Object)
    return args[0].get_method().invoke_enforced(args[0], None, args[1])


def _current_domain(ivkbl, rcvr, args, domain):
    return domain


def _executes_enforced(ivkbl, rcvr, args, domain):
    raise RuntimeError("Not yet implemented")


def _executes_unenforced(ivkbl, rcvr, args, domain):
    raise RuntimeError("Not yet implemented")


class MirrorPrimitives(Primitives):
    def install_primitives(self):
        self._install_class_primitive(Primitive("domainOf:",            self._universe, _domain_of))
        self._install_class_primitive(Primitive("setDomainOf:to:",      self._universe, _set_domain_of_to))
        self._install_class_primitive(Primitive("evaluate:in:",         self._universe, _evaluate_in))
        self._install_class_primitive(Primitive("evaluate:enforcedIn:", self._universe, _evaluated_enforced_in))
        self._install_class_primitive(Primitive("currentDomain",        self._universe, _current_domain))
        self._install_class_primitive(Primitive("executesEnforced",     self._universe, _executes_enforced))
        self._install_class_primitive(Primitive("executesUnenforced",   self._universe, _executes_unenforced))
