from rpython.rlib import jit

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.primitive import Primitive


class Block(AbstractObject):
    
    _immutable_fields_ = ["_method", "_context", "_captured_enforced"]
    
    def __init__(self, method, context, captured_enforced, domain):
        AbstractObject.__init__(self)
        self._method  = method
        self._context = context
        self._captured_enforced = captured_enforced
        self._domain  = domain
        
    def get_method(self):
        return jit.promote(self._method)
    
    def get_context(self):
        return self._context

    def get_outer_self(self):
        return self._context.get_self()
    
    def get_class(self, universe):
        return universe.blockClasses[self._method.get_number_of_arguments()]

    def get_domain(self, universe):
        return self._domain

    def set_domain(self, domain):
        self._domain = domain

    class Evaluation(Primitive):

        _immutable_fields_ = ['_number_of_arguments']

        def __init__(self, num_args, universe, invoke):
            Primitive.__init__(self, self._compute_signature_string(num_args),
                               universe, invoke)
            self._number_of_arguments = num_args

        @staticmethod
        def _compute_signature_string(num_args):
            # Compute the signature string
            signature_string = "value"
            if num_args > 1:
                signature_string += ":"
                if num_args > 2:
                    # Add extra with: selector elements if necessary
                    signature_string += "with:" * (num_args - 2)
          
            # Return the signature string
            return signature_string


def block_evaluation_primitive(num_args, universe):
    return Block.Evaluation(num_args, universe, _invoke)


## TODO: _invoke_void, is that missing???
def _invoke(ivkbl, rcvr_block, args, domain):
    assert isinstance(ivkbl, Block.Evaluation)
    method = rcvr_block.get_method()
    if rcvr_block._captured_enforced:
        return method.invoke_enforced(rcvr_block, args, domain)
    else:
        ## TODO: not sure whether this is entierly correct.
        ##       need to figure out which semantics I want/need with respect to blocks, and their lexical embedding.
        ##       should the dynamic executing context have any say in whether to execute enforced or not?
        return method.invoke_unenforced(rcvr_block, args, domain)

