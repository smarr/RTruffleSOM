from som.vmobjects.object import Object


def get_domain_for_new_objects(domain):
    assert isinstance(domain, Object)
    return domain._field1


def request_primitive_execution(domain, prim, rcvr, args):
    universe = prim.get_universe()
    return domain.send_unenforced("requestExectionOfPrimitive:with:on:",
                                  [prim, args, rcvr], universe, domain)
