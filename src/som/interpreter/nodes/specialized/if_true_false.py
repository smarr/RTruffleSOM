from ..expression_node   import ExpressionNode
from ....vmobjects.block import Block


class IfTrueIfFalseNode(ExpressionNode):

    _immutable_fields_ = ['_rcvr_expr?', '_true_expr?', '_false_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr',  '_true_expr',  '_false_expr']

    def __init__(self, rcvr_expr, true_expr, false_expr, universe,
                 executes_enforced, source_section):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._rcvr_expr  = self.adopt_child(rcvr_expr)
        self._true_expr  = self.adopt_child(true_expr)
        self._false_expr = self.adopt_child(false_expr)
        self._universe   = universe

    def execute(self, frame):
        rcvr  = self._rcvr_expr.execute(frame)
        true  = self._true_expr.execute(frame)
        false = self._false_expr.execute(frame)

        return self._do_iftrue_iffalse(rcvr, true, false,
                                       frame.get_executing_domain())

    def execute_evaluated(self, frame, rcvr, args):
        return self._do_iftrue_iffalse(rcvr, args[0], args[1],
                                       frame.get_executing_domain())

    def _value_of(self, obj, domain):
        if isinstance(obj, Block):
            if self._executes_enforced:
                return obj.get_method().invoke_enforced(obj, [], domain)
            else:
                return obj.get_method().invoke_unenforced(obj, [], domain)
        else:
            return obj

    def _do_iftrue_iffalse(self, rcvr, true, false, domain):
        if rcvr is self._universe.trueObject:
            return self._value_of(true, domain)
        else:
            assert rcvr is self._universe.falseObject
            return self._value_of(false, domain)

    def execute_void(self, frame):
        rcvr  = self._rcvr_expr.execute(frame)
        true  = self._true_expr.execute(frame)
        false = self._false_expr.execute(frame)

        return self._do_iftrue_iffalse_void(rcvr, true, false,
                                            frame.get_executing_domain())

    def execute_evaluated_void(self, frame, rcvr, args):
        return self._do_iftrue_iffalse_void(rcvr, args[0], args[1],
                                            frame.get_executing_domain())

    def _value_of_void(self, obj, domain):
        if isinstance(obj, Block):
            if self._executes_enforced:
                obj.get_method().invoke_enforced_void(obj, [], domain)
            else:
                obj.get_method().invoke_unenforced_void(obj, [], domain)

    def _do_iftrue_iffalse_void(self, rcvr, true, false, domain):
        if rcvr is self._universe.trueObject:
            self._value_of_void(true, domain)
        else:
            assert rcvr is self._universe.falseObject
            self._value_of_void(false, domain)

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (len(args) == 2 and (rcvr is node._universe.trueObject or
                                    rcvr is node._universe.falseObject) and
                selector.get_string() == "ifTrue:ifFalse:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IfTrueIfFalseNode(node._rcvr_expr, node._arg_exprs[0],
                              node._arg_exprs[1], node._universe,
                              node._executes_enforced,
                              node._source_section))


class IfNode(ExpressionNode):

    _immutable_fields_ = ['_rcvr_expr?', '_branch_expr?', '_condition',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr',  '_branch_expr']

    def __init__(self, rcvr_expr, branch_expr, condition_obj, universe,
                 executes_enforced, source_section):
        ExpressionNode.__init__(self, executes_enforced, source_section)
        self._rcvr_expr   = self.adopt_child(rcvr_expr)
        self._branch_expr = self.adopt_child(branch_expr)
        self._condition   = condition_obj
        self._universe    = universe

    def execute(self, frame):
        rcvr   = self._rcvr_expr.execute(frame)
        branch = self._branch_expr.execute(frame)
        return self._do_if(rcvr, branch, frame.get_executing_domain())
    
    def execute_void(self, frame):
        rcvr   = self._rcvr_expr.execute(frame)
        branch = self._branch_expr.execute(frame)
        return self._do_if_void(rcvr, branch, frame.get_executing_domain())

    def execute_evaluated(self, frame, rcvr, args):
        return self._do_if(rcvr, args[0], frame.get_executing_domain())
    
    def execute_evaluated_void(self, frame, rcvr, args):
        return self._do_if_void(rcvr, args[0], frame.get_executing_domain())

    def _value_of(self, obj, domain):
        if isinstance(obj, Block):
            if self._executes_enforced:
                return obj.get_method().invoke_enforced(obj, [], domain)
            else:
                return obj.get_method().invoke_unenforced(obj, [], domain)
        else:
            return obj
    
    def _value_of_void(self, obj, domain):
        if isinstance(obj, Block):
            if self._executes_enforced:
                obj.get_method().invoke_enforced_void(obj, [], domain)
            else:
                obj.get_method().invoke_unenforced_void(obj, [], domain)

    def _do_if(self, rcvr, branch, domain):
        if rcvr is self._condition:
            return self._value_of(branch, domain)
        else:
            assert (rcvr is self._universe.falseObject or
                    rcvr is self._universe.trueObject)
            return self._universe.nilObject
        
    def _do_if_void(self, rcvr, branch, domain):
        if rcvr is self._condition:
            self._value_of_void(branch, domain)
        else:
            assert (rcvr is self._universe.falseObject or
                    rcvr is self._universe.trueObject)

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        sel = selector.get_string()
        return (len(args) == 1 and (rcvr is node._universe.trueObject or
                                    rcvr is node._universe.falseObject) and
                (sel == "ifTrue:" or sel == "ifFalse:"))

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        if selector.get_string() == "ifTrue:":
            return node.replace(
                IfNode(node._rcvr_expr, node._arg_exprs[0],
                       node._universe.trueObject, node._universe,
                       node._executes_enforced,
                       node._source_section))
        else:
            assert selector.get_string() == "ifFalse:"
            return node.replace(
                IfNode(node._rcvr_expr, node._arg_exprs[0],
                       node._universe.falseObject, node._universe,
                       node._executes_enforced,
                       node._source_section))
