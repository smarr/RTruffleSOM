from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object          import Object


def create_standard_domain(nilObject):
    domain = Object(nilObject, nilObject, None)
    domain.set_domain(domain)
    set_domain_for_new_objects(domain, domain)
    return domain


def get_domain_for_new_objects(domain):
    assert isinstance(domain, Object)
    return domain._field1


def set_domain_for_new_objects(domain, a_domain):
    assert isinstance(domain,   Object)
    assert isinstance(a_domain, Object)
    domain._field1 = a_domain


def arg_array_to_som_array(args, domain, universe):
    if args is None:
        som_args = universe.nilObject
    else:
        som_args = universe.new_array_from_list(args, domain)
    return som_args


def request_primitive_execution(prim, rcvr, args, executing_domain):
    universe = prim.get_universe()
    rcvr_domain = rcvr.get_domain(universe)
    som_args = arg_array_to_som_array(args, rcvr_domain, universe)
    return rcvr_domain.send_unenforced("requestExecutionOfPrimitive:with:on:",
                                       [prim, som_args, rcvr], universe,
                                       executing_domain)


def request_execution_of(selector, rcvr, args, lookup_class, universe,
                         executing_domain):
    rcvr_domain = rcvr.get_domain(universe)
    som_args    = arg_array_to_som_array(args, rcvr_domain, universe)
    return rcvr_domain.send_unenforced("requestExecutionOf:with:on:lookup:",
                                       [selector, som_args, rcvr, lookup_class],
                                       universe, executing_domain)


def request_execution_of_void(selector, rcvr, args, lookup_class, universe,
                              executing_domain):
    rcvr_domain = rcvr.get_domain(universe)
    som_args    = arg_array_to_som_array(args, rcvr_domain, universe)
    return rcvr_domain.send_unenforced_void("requestExecutionOf:with:on:lookup:",
                                            [selector, som_args, rcvr,
                                             lookup_class],
                                            universe, executing_domain)



def read_global(symbol, rcvr, universe, executing_domain):
    return executing_domain.send_unenforced("readGlobal:for:", [symbol, rcvr],
                                            universe, executing_domain)


def read_field_of(field_idx, obj, universe, executing_domain):
    assert isinstance(obj, Object)
    assert field_idx >= 0
    rcvr_domain = obj.get_domain(universe)
    return rcvr_domain.send_unenforced("readField:of:",
                                        ## REM: need to pass on idx + 1
                                        ##      because on the SOM site,
                                        ##      we have 1-based offsets
                                        [universe.new_integer(field_idx + 1),
                                         obj],  universe, executing_domain)


def write_to_field_of(value, field_idx, obj, universe, executing_domain):
    assert isinstance(obj, Object)
    assert isinstance(value, AbstractObject)
    assert field_idx >= 0
    rcvr_domain = obj.get_domain(universe)
    return rcvr_domain.send_unenforced("write:toField:of:",
                                       [value,
                                        universe.new_integer(field_idx + 1),
                                        obj],
                                       universe, executing_domain)
