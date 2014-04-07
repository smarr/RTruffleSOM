from rpython.rlib.rrandom import Random
from rpython.rlib import jit

from som.vm.symbol_table         import SymbolTable
from som.vmobjects.domain import create_standard_domain
from som.vmobjects.object        import Object
from som.vmobjects.clazz         import Class
from som.vmobjects.array         import Array
from som.vmobjects.symbol        import Symbol
from som.vmobjects.method        import Method
from som.vmobjects.integer       import Integer
from som.vmobjects.string        import String
from som.vmobjects.block         import Block, block_evaluation_primitive
from som.vmobjects.biginteger    import BigInteger
from som.vmobjects.double        import Double

from som.vm.shell import Shell

import som.compiler.sourcecode_compiler as sourcecode_compiler

import os
import time


from rlib.exit  import Exit
from rlib.osext import path_split


class Assoc(object):

    _immutable_fields_ = ["_global_name", "_value?"]

    def __init__(self, global_name, value):
        self._global_name = global_name
        self._value       = value

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def __str__(self):
        return "(%s => %s)" % (self._global_name, self._value)


class Universe(object):
    
    CURRENT = None
    
    _immutable_fields_ = [
            "nilObject",
            "trueObject",
            "falseObject",
            "objectClass",
            "integerClass",
            "doubleClass",
            "primitiveClass"]

    def __init__(self, avoid_exit = False):
        self._symbol_table   = SymbolTable()
        
        self._globals        = {}

        self.nilObject      = None
        self.trueObject     = None
        self.falseObject    = None
        self.objectClass    = None
        self.classClass     = None
        self.metaclassClass = None
        
        self.nilClass       = None
        self.integerClass   = None
        self.bigintegerClass= None
        self.arrayClass     = None
        self.methodClass    = None
        self.symbolClass    = None
        self.primitiveClass = None
        self.systemClass    = None
        self.blockClass     = None
        self.blockClasses   = None
        self.stringClass    = None
        self.doubleClass    = None
        
        self._last_exit_code = 0
        self._avoid_exit     = avoid_exit
        self._dump_bytecodes = False
        self.classpath       = None
        self.start_time      = time.time() # a float of the time in seconds
        self.random          = Random(abs(int(time.clock() * time.time())))

        CURRENT = self

    def exit(self, error_code):
        if self._avoid_exit:
            self._last_exit_code = error_code
        else:
            raise Exit(error_code)
    
    def last_exit_code(self):
        return self._last_exit_code
    
    def execute_method(self, class_name, selector):
        self._initialize_object_system()

        clazz = self.load_class(self.symbol_for(class_name))

        # Lookup the invokable on class
        invokable = clazz.get_class(self).lookup_invokable(self.symbol_for(
            selector))

        return invokable.invoke_unenforced(clazz, None, self.standardDomain)
    
    def interpret(self, arguments):
        # Check for command line switches
        arguments = self.handle_arguments(arguments)

        # Initialize the known universe
        system_object = self._initialize_object_system()

        # Start the shell if no filename is given
        if len(arguments) == 0:
            shell = Shell(self)
            return shell.start()
        else:
            # Convert the arguments into an array
            arguments_array = self.new_array_with_strings(arguments,
                                                          self.standardDomain)

            # Lookup the initialize invokable on the system class
            initialize = self.systemClass.lookup_invokable(
                self.symbol_for("initialize:"))
            return initialize.invoke_unenforced(system_object,
                                                [arguments_array],
                                                self.standardDomain)
    
    def handle_arguments(self, arguments):
        got_classpath  = False
        remaining_args = []

        i = 0
        while i < len(arguments):
            if arguments[i] == "-cp":
                if i + 1 >= len(arguments):
                    self._print_usage_and_exit()
                self.setup_classpath(arguments[i + 1])
                i += 1    # skip class path
                got_classpath = True
            elif arguments[i] == "-d":
                self._dump_bytecodes = True
            elif arguments[i] in ["-h", "--help", "-?"]:
                self._print_usage_and_exit()
            else:
                remaining_args.append(arguments[i])
            i += 1
    
        if not got_classpath:
            # Get the default class path of the appropriate size
            self.classpath = self._setup_default_classpath()

        # check remaining args for class paths, and strip file extension
        i = 0
        while i < len(remaining_args):
            split = self._get_path_class_ext(remaining_args[i])

            if split[0] != "":  # there was a path
                self.classpath.insert(0, split[0])
        
            remaining_args[i] = split[1]
            i += 1
        
        return remaining_args
    
    def setup_classpath(self, cp):
        self.classpath = cp.split(os.pathsep)
    
    def _setup_default_classpath(self):
        return ['.']
    
    # take argument of the form "../foo/Test.som" and return
    # "../foo", "Test", "som"
    def _get_path_class_ext(self, path):
        return path_split(path)
    
    def _print_usage_and_exit(self):
        # Print the usage
        std_println("Usage: som [-options] [args...]                          ")
        std_println("                                                         ")
        std_println("where options include:                                   ")
        std_println("    -cp <directories separated by " + os.pathsep     + ">")
        std_println("        set search path for application classes")
        std_println("    -d  enable disassembling")
        std_println("    -h  print this help")

        # Exit
        self.exit(0)

    def _initialize_object_system(self):
        # Allocate the nil object and standard domain, and set them up properly
        self.nilObject = Object(None, None, None)
        self.standardDomain = create_standard_domain(self.nilObject)
        self.nilObject.set_domain(self.standardDomain)

        # Allocate the Metaclass classes
        self.metaclassClass = self.new_metaclass_class(self.standardDomain)

        # Allocate the rest of the system classes
        self.objectClass     = self.new_system_class(self.standardDomain)
        self.nilClass        = self.new_system_class(self.standardDomain)
        self.classClass      = self.new_system_class(self.standardDomain)
        self.arrayClass      = self.new_system_class(self.standardDomain)
        self.symbolClass     = self.new_system_class(self.standardDomain)
        self.methodClass     = self.new_system_class(self.standardDomain)
        self.integerClass    = self.new_system_class(self.standardDomain)
        self.bigintegerClass = self.new_system_class(self.standardDomain)
        self.primitiveClass  = self.new_system_class(self.standardDomain)
        self.stringClass     = self.new_system_class(self.standardDomain)
        self.doubleClass     = self.new_system_class(self.standardDomain)
        self.domainClass     = self.new_system_class(self.standardDomain)

        # Setup the class reference for the nil object and standard domain
        self.nilObject.set_class(self.nilClass)
        self.standardDomain.set_class(self.domainClass)

        # Initialize the system classes
        self._initialize_system_class(self.objectClass,                 None, "Object")
        self._initialize_system_class(self.classClass,      self.objectClass, "Class")
        self._initialize_system_class(self.metaclassClass,   self.classClass, "Metaclass")
        self._initialize_system_class(self.nilClass,        self.objectClass, "Nil")
        self._initialize_system_class(self.arrayClass,      self.objectClass, "Array")
        self._initialize_system_class(self.methodClass,      self.arrayClass, "Method")
        self._initialize_system_class(self.symbolClass,     self.objectClass, "Symbol")
        self._initialize_system_class(self.integerClass,    self.objectClass, "Integer")
        self._initialize_system_class(self.bigintegerClass, self.objectClass, "BigInteger")
        self._initialize_system_class(self.primitiveClass,  self.objectClass, "Primitive")
        self._initialize_system_class(self.stringClass,     self.objectClass, "String")
        self._initialize_system_class(self.doubleClass,     self.objectClass, "Double")
        self._initialize_system_class(self.domainClass,     self.objectClass, "Domain")

        # Load methods and fields into the system classes
        self._load_system_class(self.objectClass)
        self._load_system_class(self.classClass)
        self._load_system_class(self.metaclassClass)
        self._load_system_class(self.nilClass)
        self._load_system_class(self.arrayClass)
        self._load_system_class(self.methodClass)
        self._load_system_class(self.symbolClass)
        self._load_system_class(self.integerClass)
        self._load_system_class(self.bigintegerClass)
        self._load_system_class(self.primitiveClass)
        self._load_system_class(self.stringClass)
        self._load_system_class(self.doubleClass)
        self._load_system_class(self.domainClass)

        # Load the generic block class
        self.blockClass = self.load_class(self.symbol_for("Block"))

        # Setup the true and false objects
        trueClassName    = self.symbol_for("True")
        trueClass        = self.load_class(trueClassName)
        self.trueObject  = self.new_instance(trueClass, self.standardDomain)
        
        falseClassName   = self.symbol_for("False")
        falseClass       = self.load_class(falseClassName)
        self.falseObject = self.new_instance(falseClass, self.standardDomain)

        # Load the system class and create an instance of it
        self.systemClass = self.load_class(self.symbol_for("System"))
        system_object = self.new_instance(self.systemClass, self.standardDomain)

        # Put special objects and classes into the dictionary of globals
        self.set_global(self.symbol_for("nil"),    self.nilObject)
        self.set_global(self.symbol_for("true"),   self.trueObject)
        self.set_global(self.symbol_for("false"),  self.falseObject)
        self.set_global(self.symbol_for("system"), system_object)
        self.set_global(self.symbol_for("System"), self.systemClass)
        self.set_global(self.symbol_for("Block"),  self.blockClass)
        
        self.set_global(self.symbol_for("Nil"),    self.nilClass)
        
        self.set_global( trueClassName,  trueClass)
        self.set_global(falseClassName, falseClass)

        self.blockClasses = [self.blockClass] + \
                [self._make_block_class(i) for i in [1, 2, 3]]

        return system_object
    
    def symbol_for(self, string):
        # Lookup the symbol in the symbol table
        result = self._symbol_table.lookup(string)
        if result:
            return result
        
        # Create a new symbol and return it
        result = self.new_symbol(string)
        return result
    
    def new_array_with_length(self, length, domain):
        return Array(self.nilObject, length, domain)
  
    def new_array_from_list(self, values, domain):
        return Array(self.nilObject, 0, domain, values)

    def new_array_with_strings(self, strings, domain):
        # Allocate a new array with the same length as the string array
        result = self.new_array_with_length(len(strings), domain)

        # Copy all elements from the string array into the array
        for i in range(len(strings)):
            result.set_indexable_field(i, self.new_string(strings[i]))
    
        return result
    
    def new_block(self, method, context_frame, captured_enforced, domain):
        return Block(method, context_frame, captured_enforced, domain)

    def new_class(self, class_class, domain):
        # Allocate a new class and set its class to be the given class class
        return Class(self, class_class.get_number_of_instance_fields(),
                       class_class, domain)

    def new_method(self, signature, invokable, is_primitive,
                   embedded_block_method):
        return Method(signature, invokable, is_primitive, embedded_block_method,
                      self)

    def new_instance(self, instance_class, domain):
        return Object(self.nilObject, domain, instance_class,
                      instance_class.get_number_of_instance_fields())

    @staticmethod
    def new_integer(value):
        assert isinstance(value, int)
        return Integer(value)

    @staticmethod
    def new_biginteger(value):
        return BigInteger(value)

    @staticmethod
    def new_double(value):
        return Double(value)
    
    def new_metaclass_class(self, domain):
        # Allocate the metaclass classes
        result = Class(self, -1, Class(self, -1, None, domain), domain)

        # Setup the metaclass hierarchy
        result.get_class(self).set_class(result)
        return result

    @staticmethod
    def new_string(embedded_string):
        return String(embedded_string)

    def new_symbol(self, string):
        result = Symbol(string)

        # Insert the new symbol into the symbol table
        self._symbol_table.insert(result)
        return result
      
    def new_system_class(self, domain):
        # Allocate the new system class
        system_class = Class(self, -1, Class(self, -1, None, domain), domain)

        # Setup the metaclass hierarchy
        system_class.get_class(self).set_class(self.metaclassClass)
        return system_class
    
    def _initialize_system_class(self, system_class, super_class, name):
        # Initialize the superclass hierarchy
        if super_class:
            system_class.set_super_class(super_class)
            system_class.get_class(self).set_super_class(
                super_class.get_class(self))
        else:
            system_class.get_class(self).set_super_class(self.classClass)

        # Initialize the array of instance fields
        system_class.set_instance_fields(
            self.new_array_with_length(0, system_class.get_domain(self)))
        system_class.get_class(self).set_instance_fields(
            self.new_array_with_length(0, system_class.get_domain(self)))

        # Initialize the array of instance invokables
        system_class.set_instance_invokables(
            self.new_array_with_length(0, system_class.get_domain(self)))
        system_class.get_class(self).set_instance_invokables(
            self.new_array_with_length(0, system_class.get_domain(self)))

        # Initialize the name of the system class
        system_class.set_name(self.symbol_for(name))
        system_class.get_class(self).set_name(self.symbol_for(name + " class"))

        # Insert the system class into the dictionary of globals
        self.set_global(system_class.get_name(), system_class)

    def get_global(self, name):
        # Return the global with the given name if it's in the dictionary of globals
        # if not, return None
        jit.promote(self)
        assoc = self._get_global(name)
        if assoc:
            return assoc.get_value()
        else:
            return None

    @jit.elidable
    def _get_global(self, name):
        return self._globals.get(name, None)

    def set_global(self, name, value):
        self.get_globals_association(name).set_value(value)

    def has_global(self, name):
        return name in self._globals

    @jit.elidable_promote("all")
    def get_globals_association(self, name):
        assoc = self._globals.get(name, None)
        if assoc is None:
            assoc = Assoc(name, self.nilObject)
            self._globals[name] = assoc
        return assoc

    def _get_block_class(self, number_of_arguments):
        return self.blockClasses[number_of_arguments]

    def _make_block_class(self, number_of_arguments):
        # Compute the name of the block class with the given number of
        # arguments
        name = self.symbol_for("Block" + str(number_of_arguments))

        # Get the block class for blocks with the given number of arguments
        result = self._load_class(name, None)

        # Add the appropriate value primitive to the block class
        result.add_instance_primitive(block_evaluation_primitive(number_of_arguments, self))

        # Insert the block class into the dictionary of globals
        self.set_global(name, result)

        # Return the loaded block class
        return result

    def load_class(self, name):
        # Check if the requested class is already in the dictionary of globals
        result = self.get_global(name)
        if result is not None:
            return result

        # Load the class
        result = self._load_class(name, None)

        # Load primitives (if necessary) and return the resulting class
        if result and result.has_primitives():
            result.load_primitives()

        self.set_global(name, result)
        return result

    def _load_system_class(self, system_class):
        # Load the system class
        result = self._load_class(system_class.get_name(), system_class)

        if not result:
            error_println(system_class.get_name().get_string()
                   + " class could not be loaded. It is likely that the"
                   + " class path has not been initialized properly."
                   + " Please make sure that the '-cp' parameter is given on the command-line.")
            self.exit(200)

        # Load primitives if necessary
        if result.has_primitives():
            result.load_primitives()

    def _load_class(self, name, system_class):
        # Try loading the class from all different paths
        for cpEntry in self.classpath:
            try:
                # Load the class from a file and return the loaded class
                result = sourcecode_compiler.compile_class_from_file(cpEntry, name.get_string(), system_class, self)
                if self._dump_bytecodes:
                    from som.compiler.disassembler import dump
                    dump(result.get_class(self))
                    dump(result)

                return result
            except IOError:
                # Continue trying different paths
                pass

        # The class could not be found.
        return None
    
    def load_shell_class(self, stmt):
        # Load the class from a stream and return the loaded class
        result = sourcecode_compiler.compile_class_from_string(stmt, None, self)
        if self._dump_bytecodes:
            from som.compiler.disassembler import dump
            dump(result)
        return result


def error_print(msg):
    os.write(2, msg or "")


def error_println(msg = ""):
    os.write(2, msg + "\n")


def std_print(msg):
    os.write(1, msg or "")


def std_println(msg = ""):
    os.write(1, msg + "\n")


def main(args):
    u = Universe()
    u.interpret(args[1:])
    u.exit(0)


def get_current():
    return Universe.CURRENT

if __name__ == '__main__':
    import sys
    try:
        main(sys.argv)
    except Exit as e:
        sys.exit(e.code)
