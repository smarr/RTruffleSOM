from rpython.rlib import jit


class AbstractObject(object):
    
    def __init__(self):
        pass
        
    def send_enforced(self, selector_string, arguments, universe, domain):
        selector = universe.symbol_for(selector_string)
        invokable = self.get_class(universe).lookup_invokable(selector)
        return invokable.invoke_enforced(self, arguments, domain)

    def send_enforced_void(self, selector_string, arguments, universe, domain):
        selector = universe.symbol_for(selector_string)
        invokable = self.get_class(universe).lookup_invokable(selector)
        invokable.invoke_enforced_void(self, arguments, domain)

    def send_unenforced(self, selector_string, arguments, universe, domain):
        selector = universe.symbol_for(selector_string)
        invokable = self.get_class(universe).lookup_invokable(selector)
        return invokable.invoke_unenforced(self, arguments, domain)

    def send_unenforced_void(self, selector_string, arguments, universe, domain):
        # Turn the selector string into a selector
        selector = universe.symbol_for(selector_string)
        invokable = self.get_class(universe).lookup_invokable(selector)
        invokable.invoke_unenforced_void(self, arguments, domain)

    @staticmethod
    @jit.unroll_safe
    def _prepare_dnu_arguments(arguments, selector, universe, domain):
        # Compute the number of arguments
        selector = jit.promote(selector)
        universe = jit.promote(universe)
        number_of_arguments = selector.get_number_of_signature_arguments() - 1 ## without self
        assert number_of_arguments == len(arguments)

        ## TODO: make sure that we select the right domain here as owner
        ##       this needs to be confirmed after all that is fixed
        arguments_array = universe.new_array_with_length(number_of_arguments, domain)
        for i in range(0, number_of_arguments):
            arguments_array.set_indexable_field(i, arguments[i])
        args = [selector, arguments_array]
        return args

    def send_does_not_understand_enforced(self, selector, arguments, universe, domain):
        args = self._prepare_dnu_arguments(arguments, selector, universe, domain)
        return self.send_enforced("doesNotUnderstand:arguments:", args, universe, domain)

    def send_does_not_understand_enforced_void(self, selector, arguments, universe, domain):
        args = self._prepare_dnu_arguments(arguments, selector, universe, domain)
        self.send_enforced_void("doesNotUnderstand:arguments:", args, universe, domain)

    def send_does_not_understand_unenforced(self, selector, arguments, universe, domain):
        args = self._prepare_dnu_arguments(arguments, selector, universe, domain)
        return self.send_unenforced("doesNotUnderstand:arguments:", args, universe, domain)

    def send_does_not_understand_unenforced_void(self, selector, arguments, universe, domain):
        args = self._prepare_dnu_arguments(arguments, selector, universe, domain)
        self.send_unenforced_void("doesNotUnderstand:arguments:", args,
                                  universe, domain)

    def send_unknown_global_enforced(self, global_name, universe, domain):
        arguments = [global_name]
        return self.send_enforced("unknownGlobal:", arguments, universe, domain)

    def send_unknown_global_unenforced(self, global_name, universe, domain):
        arguments = [global_name]
        return self.send_unenforced("unknownGlobal:", arguments, universe, domain)

    def send_escaped_block_enforced(self, block, universe, domain):
        arguments = [block]
        return self.send_enforced("escapedBlock:", arguments, universe, domain)

    def send_escaped_block_unenforced(self, block, universe, domain):
        arguments = [block]
        return self.send_unenforced("escapedBlock:", arguments, universe, domain)

    def get_class(self, universe):
        raise NotImplementedError("Subclasses need to implement get_class(universe).")

    def has_domain(self):
        return True

    def get_domain(self, universe):
        raise NotImplementedError("Subclasses need to implement get_domain(universe).")

    def set_domain(self, domain):
        raise NotImplementedError("Subclasses need to implement set_domain(domain).")

    def is_invokable(self):
        return False

    def __str__(self):
        from som.vm.universe import get_current
        return "a " + self.get_class(get_current()).get_name().get_string()
