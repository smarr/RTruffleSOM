from som.vmobjects.object import Object


class Domain(Object):

    NUMBER_OF_OBJECT_FIELDS = 1  ## domainForNewObjects

    def __init__(self, nilObject, obj_class, domain):
        Object.__init__(self, nilObject, self.NUMBER_OF_OBJECT_FIELDS,
                        obj_class, domain)
        assert nilObject is not None
        assert obj_class is not None
        assert domain    is not None

    def get_domain_for_new_objects(self):
        return self._field1
