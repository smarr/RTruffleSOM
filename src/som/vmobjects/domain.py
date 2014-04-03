from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object import Object


def get_domain_for_new_objects(domain):
    assert isinstance(domain, Object)
    return domain._field1


def request_primitive_execution(domain, prim, rcvr, args):
    universe = prim.get_universe()
    if args is None:
        som_args = universe.nilObject
    else:
        som_args = universe.new_array_from_list(args, domain)
    return domain.send_unenforced("requestExecutionOfPrimitive:with:on:",
                                  [prim, som_args, rcvr], universe, domain)


def read_global(domain, symbol, universe):
    return domain.send_unenforced("readGlobal:", [symbol], universe, domain)


def read_field_of(domain, field_idx, obj, universe):
    assert isinstance(obj, Object)
    assert field_idx >= 0
    return domain.send_unenforced("readField:of:",
                                  ## REM: need to pass on idx + 1 because on the
                                  ##      SOM site, we have 1-based offsets
                                  [universe.new_integer(field_idx + 1), obj],
                                  universe, domain)


def write_to_field_of(domain, value, field_idx, obj, universe):
    assert isinstance(obj, Object)
    assert isinstance(value, AbstractObject)
    assert field_idx >= 0
    return domain.send_unenforced("write:toField:of:",
                                  [value, universe.new_integer(field_idx + 1),
                                   obj],
                                  universe, domain)
