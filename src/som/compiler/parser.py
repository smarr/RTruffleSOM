from rtruffle.source_section import SourceSection

from ..interpreter.nodes.block_node       import BlockNode, BlockNodeWithContext
from ..interpreter.nodes.global_read_node import \
    UninitializedGlobalReadNodeUnenforced
from ..interpreter.nodes.literal_node     import LiteralNode
from ..interpreter.nodes.message_node     import \
    UninitializedMessageNodeUnenforced
from ..interpreter.nodes.return_non_local_node import ReturnNonLocalNode
from ..interpreter.nodes.sequence_node    import SequenceNode

from .lexer                     import Lexer
from .method_generation_context import MethodGenerationContext
from som.interpreter.nodes.enforced.global_read_node import \
    UninitializedGlobalReadNodeEnforced
from som.interpreter.nodes.enforced.message_node_enforced import \
    UninitializedMessageNodeEnforced
from .symbol                    import Symbol, symbol_as_str

from ..vmobjects.integer import integer_value_fits


class ParseError(BaseException):
    def __init__(self, message, expected_sym, parser):
        self._message           = message
        self._source_coordinate = parser._lexer.get_source_coordinate()
        self._text              = parser._text
        self._raw_buffer        = parser._lexer.get_raw_buffer()
        self._file_name         = parser._file_name
        self._expected_sym      = expected_sym
        self._found_sym         = parser._sym

    def _is_printable_symbol(self):
        return (self._found_sym == Symbol.Integer or
                self._found_sym == Symbol.Double  or
                self._found_sym >= Symbol.STString)

    def _expected_sym_str(self):
        return symbol_as_str(self._expected_sym)

    def __str__(self):
        msg = "%(file)s:%(line)d:%(column)d: error: " + self._message
        if self._is_printable_symbol():
            found = "%s (%s)" % (symbol_as_str(self._found_sym), self._text)
        else:
            found = symbol_as_str(self._found_sym)
        msg += ": %s" % self._raw_buffer

        expected = self._expected_sym_str()

        return (msg % {
            'file'       : self._file_name,
            'line'       : self._source_coordinate.get_start_line(),
            'column'     : self._source_coordinate.get_start_column(),
            'expected'   : expected,
            'found'      : found})


class ParseErrorSymList(ParseError):

    def __init__(self, message, expected_syms, parser):
        ParseError.__init__(self, message, 0, parser)
        self._expected_syms = expected_syms

    def _expected_sym_str(self):
        return  ", ".join([symbol_as_str(x) for x in self._expected_syms])


class Parser(object):
    
    _single_op_syms        = [Symbol.Not,  Symbol.And,  Symbol.Or,    Symbol.Star,
                              Symbol.Div,  Symbol.Mod,  Symbol.Plus,  Symbol.Equal,
                              Symbol.More, Symbol.Less, Symbol.Comma, Symbol.At,
                              Symbol.Per,  Symbol.NONE]
    
    _binary_op_syms        = [Symbol.Or,   Symbol.Comma, Symbol.Minus, Symbol.Equal,
                              Symbol.Not,  Symbol.And,   Symbol.Or,    Symbol.Star,
                              Symbol.Div,  Symbol.Mod,   Symbol.Plus,  Symbol.Equal,
                              Symbol.More, Symbol.Less,  Symbol.Comma, Symbol.At,
                              Symbol.Per,  Symbol.NONE]
    
    _keyword_selector_syms = [Symbol.Keyword, Symbol.KeywordSequence]
  
    def __init__(self, reader, file_name, universe):
        self._universe = universe
        self._source_reader = reader
        self._file_name = file_name
        self._lexer    = Lexer(reader)
        self._sym      = Symbol.NONE
        self._text     = None
        self._next_sym = Symbol.NONE
        self._get_symbol_from_lexer()

    def classdef(self, cgenc):
        cgenc.set_name(self._universe.symbol_for(self._text))
        self._expect(Symbol.Identifier)
        self._expect(Symbol.Equal)
 
        self._superclass(cgenc)
  
        self._expect(Symbol.NewTerm)
        self._instance_fields(cgenc)
        
        while (self._sym_is_identifier() or self._sym == Symbol.Keyword or
               self._sym == Symbol.OperatorSequence or
               self._sym_in(self._binary_op_syms)):
            mgenc = MethodGenerationContext(self._universe)
            mgenc.set_holder(cgenc)
            mgenc.add_argument("self")
         
            method_body_en, method_body_un = self._method(mgenc)
         
            if mgenc.is_primitive():
                cgenc.add_instance_method(mgenc.assemble_primitive())
            else:
                cgenc.add_instance_method(
                    mgenc.assemble(method_body_en, method_body_un))

        if self._accept(Symbol.Separator):
            cgenc.set_class_side(True)
            self._class_fields(cgenc)
            
            while (self._sym_is_identifier()      or
                   self._sym == Symbol.Keyword    or
                   self._sym == Symbol.OperatorSequence or
                   self._sym_in(self._binary_op_syms)):
                mgenc = MethodGenerationContext(self._universe)
                mgenc.set_holder(cgenc)
                mgenc.add_argument("self")
         
                method_body_en, method_body_un = self._method(mgenc)
         
                if mgenc.is_primitive():
                    cgenc.add_class_method(mgenc.assemble_primitive())
                else:
                    cgenc.add_class_method(
                        mgenc.assemble(method_body_en, method_body_un))
        
        self._expect(Symbol.EndTerm)

    def _superclass(self, cgenc):
        if self._sym == Symbol.Identifier:
            super_name = self._universe.symbol_for(self._text)
            self._accept(Symbol.Identifier)
        else:
            super_name = self._universe.symbol_for("Object")
        
        cgenc.set_super_name(super_name)
 
        # Load the super class, if it is not nil (break the dependency cycle)
        if super_name.get_string() != "nil":
            super_class = self._universe.load_class(super_name)
            if not super_class:
                raise ParseError("Super class %s could not be loaded"
                                 % super_name.get_string(), Symbol.NONE, self)
            cgenc.set_instance_fields_of_super(
                super_class.get_instance_fields())
            cgenc.set_class_fields_of_super(
                super_class.get_class(self._universe).get_instance_fields())
        else:
            # TODO: figure out what this is
            #raise Exception("What is going on here, not in Java, and I don't think we still got a 'class' field")
            # WARNING:
            # We hardcode here the field names for Class
            # since Object class superclass = Class
            # We avoid here any kind of dynamic solution to avoid further
            # complexity. However, that makes it static, it is going to make it
            #  harder to change the definition of Class and Object
            field_names_of_class = ["class", "superClass", "name",
                                    "instanceFields", "instanceInvokables"]
            field_names = self._universe.new_array_with_strings(
                field_names_of_class, self._universe.standardDomain)
            cgenc.set_class_fields_of_super(field_names)

    def _sym_in(self, symbol_list):
        return self._sym in symbol_list

    def _sym_is_identifier(self):
        return self._sym == Symbol.Identifier or self._sym == Symbol.Primitive

    def _accept(self, s):
        if self._sym == s:
            self._get_symbol_from_lexer()
            return True
        return False

    def _accept_one_of(self, symbol_list):
        if self._sym_in(symbol_list):
            self._get_symbol_from_lexer()
            return True
        return False
  
    def _expect(self, s):
        if self._accept(s):
            return True
        raise ParseError("Unexpected symbol. Expected %(expected)s, but found "
                         "%(found)s", s, self)

    def _expect_one_of(self, symbol_list):
        if self._accept_one_of(symbol_list):
            return True
        raise ParseErrorSymList("Unexpected symbol. Expected one of "
                                "%(expected)s, but found %(found)s",
                                symbol_list, self)

    def _instance_fields(self, cgenc):
        if self._accept(Symbol.Or):
            while self._sym_is_identifier():
                var = self._variable()
                cgenc.add_instance_field(self._universe.symbol_for(var))
            self._expect(Symbol.Or)
 
    def _class_fields(self, cgenc):
        if self._accept(Symbol.Or):
            while self._sym_is_identifier():
                var = self._variable()
                cgenc.add_class_field(self._universe.symbol_for(var))
            self._expect(Symbol.Or)

    def _get_source_section(self, coord):
        return SourceSection(
            self._source_reader, "method", coord,
            self._lexer.get_number_of_characters_read(),
            self._file_name)

    def _assign_source(self, node, coord):
        node.assign_source_section(self._get_source_section(coord))
        return node

    def _method(self, mgenc):
        self._pattern(mgenc)
        self._expect(Symbol.Equal)

        self._unenforced_annotation(mgenc)

        if self._sym == Symbol.Primitive:
            mgenc.set_primitive()
            return self._primitive_block()
        else:
            return self._method_block(mgenc)

    def _unenforced_annotation(self, mgenc):
        if self._sym == Symbol.Identifier:
            if self._text == "unenforced":
                self._accept(Symbol.Identifier)
                mgenc.set_unenforced()
            else:
                raise ParseError("Unexpected identifier: %s" % self._text,
                                 Symbol.Identifier, self)

    def _primitive_block(self):
        self._accept(Symbol.Primitive)
        return None, None

    def _pattern(self, mgenc):
        if self._sym_is_identifier():
            self._unary_pattern(mgenc)
        elif self._sym == Symbol.Keyword:
            self._keyword_pattern(mgenc)
        else:
            self._binary_pattern(mgenc)

    def _unary_pattern(self, mgenc):
        mgenc.set_signature(self._unary_selector())

    def _binary_pattern(self, mgenc):
        mgenc.set_signature(self._binary_selector())
        mgenc.add_argument_if_absent(self._argument())
 
    def _keyword_pattern(self, mgenc):
        kw = self._keyword()
        mgenc.add_argument_if_absent(self._argument())
        
        while self._sym == Symbol.Keyword:
            kw += self._keyword()
            mgenc.add_argument_if_absent(self._argument())
            
        mgenc.set_signature(self._universe.symbol_for(kw))

    def _method_block(self, mgenc):
        self._expect(Symbol.NewTerm)
        method_body = self._block_contents(mgenc)
        self._expect(Symbol.EndTerm)
        return method_body

    def _unary_selector(self):
        return self._universe.symbol_for(self._identifier())
 
    def _binary_selector(self):
        s = self._text
 
        if    self._accept(Symbol.Or):                     pass
        elif  self._accept(Symbol.Comma):                  pass
        elif  self._accept(Symbol.Minus):                  pass
        elif  self._accept(Symbol.Equal):                  pass
        elif  self._accept_one_of(self._single_op_syms):   pass
        elif  self._accept(Symbol.OperatorSequence):       pass
        else: self._expect(Symbol.NONE)
  
        return self._universe.symbol_for(s)
 
    def _identifier(self):
        s = self._text
        is_primitive = self._accept(Symbol.Primitive)
        if not is_primitive:
            self._expect(Symbol.Identifier)
        return s

    def _keyword(self):
        s = self._text
        self._expect(Symbol.Keyword)
        return s

    def _argument(self):
        return self._variable()

    def _block_contents(self, mgenc):
        if self._accept(Symbol.Or):
            self._locals(mgenc)
            self._expect(Symbol.Or)
  
        return self._block_body(mgenc)

    def _locals(self, mgenc):
        while self._sym_is_identifier():
            mgenc.add_local_if_absent(self._variable())

    def _self_read(self, mgenc):
        self_coord = self._lexer.get_source_coordinate()
        self_enforced, self_unenforced = self._variable_read(mgenc, "self")

        self._assign_source(self_enforced,   self_coord)
        self._assign_source(self_unenforced, self_coord)
        return self_enforced, self_unenforced

    def _block_body(self, mgenc):
        coordinate = self._lexer.get_source_coordinate()
        expressions_enforced   = []
        expressions_unenforced = []

        while True:
            if self._accept(Symbol.Exit):
                enforced, unenforced = self._result(mgenc)
                expressions_enforced.append(enforced)
                expressions_unenforced.append(unenforced)
                return self._create_sequence_node(coordinate,
                                                  expressions_enforced,
                                                  expressions_unenforced)
            elif self._sym == Symbol.EndBlock:
                return self._create_sequence_node(coordinate,
                                                  expressions_enforced,
                                                  expressions_unenforced)
            elif self._sym == Symbol.EndTerm:
                # the end of the method has been found (EndTerm) - make it
                # implicitly return "self"
                enforced, unenforced = self._self_read(mgenc)
                expressions_enforced.append(enforced)
                expressions_unenforced.append(unenforced)
                return self._create_sequence_node(coordinate,
                                                  expressions_enforced,
                                                  expressions_unenforced)

            enforced, unenforced = self._expression(mgenc)
            expressions_enforced.append(enforced)
            expressions_unenforced.append(unenforced)
            self._accept(Symbol.Period)

    def _create_sequence_node(self, coordinate, exprs_enforced, exprs_unenforced):
        if not exprs_unenforced:
            nil_enforced   = UninitializedGlobalReadNodeEnforced(
                self._universe.symbol_for("nil"), self._universe)
            nil_unenforced = UninitializedGlobalReadNodeUnenforced(
                self._universe.symbol_for("nil"), self._universe)
            return self._assign_source(nil_enforced, coordinate),\
                   self._assign_source(nil_unenforced, coordinate)
        if len(exprs_unenforced) == 1:
            return exprs_enforced[0], exprs_unenforced[0]

        return SequenceNode(exprs_enforced[:],   True,  self._get_source_section(coordinate)),\
               SequenceNode(exprs_unenforced[:], False, self._get_source_section(coordinate))

    def _result(self, mgenc):
        enforced, unenforced = self._expression(mgenc)
        coord = self._lexer.get_source_coordinate()

        self._accept(Symbol.Period)

        if mgenc.is_block_method():
            enforced_return   = ReturnNonLocalNode(mgenc.get_outer_self_context_level(),
                                                   enforced,   self._universe, True)
            unenforced_return = ReturnNonLocalNode(mgenc.get_outer_self_context_level(),
                                                   unenforced, self._universe, False)
            mgenc.make_catch_non_local_return()
            return self._assign_source(enforced_return,   coord), \
                   self._assign_source(unenforced_return, coord)
        else:
            return enforced, unenforced

    def _expression(self, mgenc):
        self._peek_for_next_symbol_from_lexer()
 
        if self._next_sym == Symbol.Assign:
            return self._assignation(mgenc)
        else:
            return self._evaluation(mgenc)

    def _assignation(self, mgenc):
        return self._assignments(mgenc)

    def _assignments(self, mgenc):
        coord = self._lexer.get_source_coordinate()

        if not self._sym_is_identifier():
            raise ParseError("Assignments should always target variables or"
                             " fields, but found instead a %(found)s",
                             Symbol.Identifier, self)

        variable_name = self._assignment()
        self._peek_for_next_symbol_from_lexer()

        if self._next_sym == Symbol.Assign:
            value_en, value_un = self._assignments(mgenc)
        else:
            value_en, value_un = self._evaluation(mgenc)

        write_en, write_un = self._variable_write(mgenc, variable_name, value_en, value_un)
        return self._assign_source(write_en, coord),\
               self._assign_source(write_un, coord)
 
    def _assignment(self):
        var_name = self._variable()
        self._expect(Symbol.Assign)
        return var_name

    def _evaluation(self, mgenc):
        enforced, unenforced = self._primary(mgenc)
 
        if (self._sym_is_identifier()            or
            self._sym == Symbol.Keyword          or 
            self._sym == Symbol.OperatorSequence or
            self._sym_in(self._binary_op_syms)):
            enforced, unenforced = self._messages(mgenc, enforced, unenforced)
        return enforced, unenforced
 
    def _primary(self, mgenc):
        if self._sym_is_identifier():
            coordinate = self._lexer.get_source_coordinate()
            var_name = self._variable()
            read_en, read_un = self._variable_read(mgenc, var_name)
            return self._assign_source(read_en, coordinate), \
                   self._assign_source(read_un, coordinate)

        if self._sym == Symbol.NewTerm:
            return self._nested_term(mgenc)

        if self._sym == Symbol.NewBlock:
            coordinate = self._lexer.get_source_coordinate()
            bgenc = MethodGenerationContext(self._universe)
            bgenc.set_is_block_method(True)
            bgenc.set_holder(mgenc.get_holder())
            bgenc.set_outer(mgenc)
 
            block_body_en, block_body_un = self._nested_block(bgenc)
            block_method = bgenc.assemble(block_body_en, block_body_un)
            mgenc.add_embedded_block_method(block_method)

            if bgenc.requires_context():
                block_en = BlockNodeWithContext(block_method,
                                                self._universe, True)
                block_un = BlockNodeWithContext(block_method,
                                                self._universe, False)
            else:
                block_en = BlockNode(block_method, self._universe,  True)
                block_un = BlockNode(block_method, self._universe, False)
            return self._assign_source(block_en, coordinate), \
                   self._assign_source(block_un, coordinate)

        return self._literal()
 
    def _variable(self):
        return self._identifier()
 
    def _messages(self, mgenc, receiver_en, receiver_un):
        msg_en = receiver_en
        msg_un = receiver_un

        while self._sym_is_identifier():
            msg_en, msg_un = self._unary_message(msg_en, msg_un)

        while (self._sym == Symbol.OperatorSequence or
               self._sym_in(self._binary_op_syms)):
            msg_en, msg_un = self._binary_message(mgenc, msg_en, msg_un)
    
        if self._sym == Symbol.Keyword:
            msg_en, msg_un = self._keyword_message(mgenc, msg_en, msg_un)
        
        return msg_en, msg_un

    def _unary_message(self, receiver_en, receiver_un):
        coord = self._lexer.get_source_coordinate()
        selector = self._unary_selector()
        msg_en = UninitializedMessageNodeEnforced(selector,   self._universe,
                                                  receiver_en, [])
        msg_un = UninitializedMessageNodeUnenforced(selector, self._universe,
                                                    receiver_un, [])
        return self._assign_source(msg_en, coord), \
               self._assign_source(msg_un, coord)

    def _binary_message(self, mgenc, receiver_en, receiver_un):
        coord    = self._lexer.get_source_coordinate()
        selector = self._binary_selector()
        operand_en, operand_un = self._binary_operand(mgenc)

        msg_en = UninitializedMessageNodeEnforced(selector, self._universe,
                                                  receiver_en, [operand_en])
        msg_un = UninitializedMessageNodeUnenforced(selector, self._universe,
                                                    receiver_un, [operand_un])
        return self._assign_source(msg_en, coord), \
               self._assign_source(msg_un, coord)

    def _binary_operand(self, mgenc):
        operand_en, operand_un = self._primary(mgenc)
 
        while self._sym_is_identifier():
            operand_en, operand_un = self._unary_message(operand_en, operand_un)
        return operand_en, operand_un

    def _keyword_message(self, mgenc, receiver_en, receiver_un):
        coord = self._lexer.get_source_coordinate()
        arguments_en = []
        arguments_un = []
        keyword      = []

        while self._sym == Symbol.Keyword:
            keyword.append(self._keyword())
            arg_en, arg_un = self._formula(mgenc)
            arguments_en.append(arg_en)
            arguments_un.append(arg_un)

        selector = self._universe.symbol_for("".join(keyword))
        msg_en = UninitializedMessageNodeEnforced(selector, self._universe,
                                                  receiver_en, arguments_en[:])
        msg_un = UninitializedMessageNodeUnenforced(selector, self._universe,
                                                    receiver_un,
                                                    arguments_un[:])
        return self._assign_source(msg_en, coord), \
               self._assign_source(msg_un, coord)

    def _formula(self, mgenc):
        operand_en, operand_un = self._binary_operand(mgenc)

        while (self._sym == Symbol.OperatorSequence or
               self._sym_in(self._binary_op_syms)):
            operand_en, operand_un = self._binary_message(mgenc, operand_en,
                                                          operand_un)
        return operand_en, operand_un

    def _nested_term(self, mgenc):
        self._expect(Symbol.NewTerm)
        exp_en, exp_un = self._expression(mgenc)
        self._expect(Symbol.EndTerm)
        return exp_en, exp_un

    def _literal(self):
        if self._sym == Symbol.Pound:
            return self._literal_symbol()
        if self._sym == Symbol.STString:
            return self._literal_string()
        return self._literal_number()

    def _literal_number(self):
        coord = self._lexer.get_source_coordinate()

        if self._sym == Symbol.Minus:
            lit_en, lit_un = self._negative_decimal()
        else:
            lit_en, lit_un = self._literal_decimal(False)

        return self._assign_source(lit_en, coord), \
               self._assign_source(lit_un, coord)
  
    def _literal_decimal(self, negate_value):
        if self._sym == Symbol.Integer:
            return self._literal_integer(negate_value)
        else:
            assert self._sym == Symbol.Double
            return self._literal_double(negate_value)

    def _negative_decimal(self):
        self._expect(Symbol.Minus)
        return self._literal_decimal(True)
 
    def _literal_integer(self, negate_value):
        try:
            i = int(self._text)
            if negate_value:
                i = 0 - i
        except ValueError:
            raise ParseError("Could not parse integer. "
                             "Expected a number but got '%s'" % self._text,
                             Symbol.NONE, self)
        self._expect(Symbol.Integer)

        if integer_value_fits(i):
            val = self._universe.new_integer(i)
        else:
            val = self._universe.new_biginteger(i)

        return LiteralNode(val, True), \
            LiteralNode(val, False)

    def _literal_double(self, negate_value):
        try:
            f = float(self._text)
            if negate_value:
                f = 0.0 - f
        except ValueError:
            raise ParseError("Could not parse double. "
                             "Expected a number but got '%s'" % self._text,
                             Symbol.NONE, self)
        self._expect(Symbol.Double)
        val = self._universe.new_double(f)
        return LiteralNode(val, True), \
            LiteralNode(val, False)
 
    def _literal_symbol(self):
        coord = self._lexer.get_source_coordinate()

        self._expect(Symbol.Pound)
        if self._sym == Symbol.STString:
            s    = self._string()
            symb = self._universe.symbol_for(s)
        else:
            symb = self._selector()
      
        lit_en = LiteralNode(symb, True,  self._get_source_section(coord))
        lit_un = LiteralNode(symb, False, self._get_source_section(coord))
        return lit_en, lit_un

    def _literal_string(self):
        coord = self._lexer.get_source_coordinate()
        s = self._string()
     
        string = self._universe.new_string(s)
        lit_en = LiteralNode(string, True)
        lit_un = LiteralNode(string, False)
        return self._assign_source(lit_en, coord), \
               self._assign_source(lit_un, coord)
     
    def _selector(self):
        if (self._sym == Symbol.OperatorSequence or
            self._sym_in(self._single_op_syms)):
            return self._binary_selector()
        if (self._sym == Symbol.Keyword or
            self._sym == Symbol.KeywordSequence):
            return self._keyword_selector()
        return self._unary_selector()
 
    def _keyword_selector(self):
        s = self._text
        self._expect_one_of(self._keyword_selector_syms)
        symb = self._universe.symbol_for(s)
        return symb
 
    def _string(self):
        s = self._text
        self._expect(Symbol.STString)
        return s

    def _nested_block(self, mgenc):
        self._expect(Symbol.NewBlock)

        mgenc.add_argument_if_absent("$blockSelf")

        if self._sym == Symbol.Colon:
            self._block_pattern(mgenc)

        # generate Block signature
        block_sig = "$blockMethod"
        arg_size = mgenc.get_number_of_arguments()
        block_sig += ":" * (arg_size - 1)

        mgenc.set_signature(self._universe.symbol_for(block_sig))
 
        expr_en, expr_un = self._block_contents(mgenc)
        self._expect(Symbol.EndBlock)
        return expr_en, expr_un
 
    def _block_pattern(self, mgenc):
        self._block_arguments(mgenc)
        self._expect(Symbol.Or)

    def _block_arguments(self, mgenc):
        self._expect(Symbol.Colon)
        mgenc.add_argument_if_absent(self._argument())
  
        while self._sym == Symbol.Colon:
            self._accept(Symbol.Colon)
            mgenc.add_argument_if_absent(self._argument())
 
    def _variable_read(self, mgenc, variable_name):
        # 'super' needs to be handled separately
        if variable_name == "super":
            variable = mgenc.get_variable("self")
            return variable.get_super_read_node(
                mgenc.get_outer_self_context_level(),
                mgenc.get_holder().get_name(),
                mgenc.get_holder().is_class_side(),
                self._universe)

        # first lookup in local variables, or method arguments
        variable = mgenc.get_variable(variable_name)
        if variable:
            return variable.get_read_node(
                mgenc.get_context_level(variable_name))

        # otherwise, it might be an object field
        var_symbol = self._universe.symbol_for(variable_name)
        field_read_en, field_read_un = mgenc.get_object_field_read(var_symbol)
        if field_read_en:
            return field_read_en, field_read_un

        # nope, so, it is a global?
        return mgenc.get_global_read(var_symbol)

    def _variable_write(self, mgenc, variable_name, exp_en, exp_un):
        variable = mgenc.get_local(variable_name)
        if variable:
            return variable.get_write_node(
                mgenc.get_context_level(variable_name), exp_en, exp_un)

        field_name = self._universe.symbol_for(variable_name)
        field_write_en, field_write_un = mgenc.get_object_field_write(
            field_name, exp_en, exp_un)
        if field_write_en:
            return field_write_en, field_write_un
        else:
            raise RuntimeError("Neither a variable nor a field found in current"
                               " scope that is named " + variable_name +
                               ". Arguments are read-only.")

    def _get_symbol_from_lexer(self):
        self._sym  = self._lexer.get_sym()
        self._text = self._lexer.get_text()
    
    def _peek_for_next_symbol_from_lexer(self):
        self._next_sym = self._lexer.peek()

