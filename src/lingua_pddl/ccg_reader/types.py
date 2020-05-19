import re
import copy

class Task(object):
    def __init__(self, name, arguments):
        self.method_arguments = arguments

        self.method_argument_types = {}
        
        if arguments:
            for arg in re.findall(r'\(([^\)]+)', name)[0].split(', '):
                type_name, var = arg.split()
                self.method_argument_types[var] = type_name

        self.method_name = name.split('(')[0]
        self.task_name = name

    def get_name(self):
        return self.method_name + '(' + ', '.join([self.method_argument_types[key] + ' ' + key
                                                   for key in self.method_argument_types]) + ')'

    def get_argument_keys(self):
        for arg in self.method_arguments:
            yield arg

    def get_arguments(self):
        return list(self.method_arguments.values())

    def get_argument(self, key):
        return self.method_arguments[key]

    def set_argument(self, key, value):
        self.method_arguments[key] = value

    def get_argument_type(self, key):
        return self.method_argument_types[key]

    def set_argument_type(self, key, value):
        self.method_argument_types[key] = value

    def is_valid(self):
        for key in self.method_arguments:
            if not self.method_arguments[key] or not self.method_arguments[key].is_valid():
                return False
        return True

    def __str__(self):
        outstr = self.get_name()
        for key in self.method_arguments:
            outstr += '\n\t{}:'.format(key)
            for line in str(self.method_arguments[key]).split('\n'):
                outstr += '\n\t\t{}'.format(line)
         
        return outstr

    def __bool__(self):
        return self.is_valid()

    def toJSON(self):
        return {
            'type': 'task',
            'task_name': self.task_name,
            'method_name': self.method_name,
            'argument_types': self.method_argument_types,
            'arguments': { key: self.method_arguments[key].toJSON() for key in self.method_arguments }
        }
    #def __deepcopy__(self, memodict={}):
    #    return Task(self.task_name, {arg_id: copy.deepcopy(self.method_arguments[arg_id]) for arg_id in self.method_arguments})

class Conjunction(object):
    def __init__(self, tag, left, right):
        self.tag = tag
        self.left = left
        self.right = right

        self.id = None

    def get_type_name(self):
        if isinstance(self.left, Object):
            return self.left.get_type_name()
        return None

    def get_descriptor(self):
        return str(self)

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def ground(self, state):
        if not self.left.is_grounded():
            self.left.ground(state)

        if not self.right.is_grounded():
            self.right.ground(state)

        self.set_id(parse(state, '({0} {1} {2})'.format(self.tag,
                                                        self.left.get_id(),
                                                        self.right.get_id())))

    def is_grounded(self):
        return self.id is not None

    def get_left(self):
        return self.left

    def set_left(self, left):
        self.left = left

    def get_right(self):
        return self.right

    def set_right(self, right):
        self.right = right

    def __iter__(self):
        if not isinstance(self.left, Conjunction):
            yield self.left
        else:
            for item in self.left:
                yield item
        if not isinstance(self.right, Conjunction):
            yield self.right
        else:
            for item in self.right:
                yield item

    def is_valid(self):
        return self.left and self.left.is_valid() and self.right and self.right.is_valid()

    def __str__(self):
        outstr = self.tag
        
        outstr += '\n\t-'
        for line in str(self.left).split('\n'):
            outstr += '\n\t\t{}'.format(line)
            
        outstr += '\n\t-'
        for line in str(self.right).split('\n'):
            outstr += '\n\t\t{}'.format(line)
            
        return outstr

    def __bool__(self):
        return self.is_valid()

    def toJSON(self):
        return [item.toJSON() for item in self]

class Conditional(object):
    def __init__(self, antecedent, consequent, persistent, inverted, mappings = []):
        self.antecedent = antecedent
        self.consequent = consequent

        self.persistent = persistent
        self.inverted = inverted

        self.mappings = mappings

    def get_antecedent(self):
        return self.antecedent

    def set_antecedent(self, antecedent):
        self.antecedent = antecedent

    def get_consequent(self):
        return self.consequent

    def set_consequent(self, consequent):
        self.consequent = consequent

    def is_persistent(self):
        return self.persistent

    def is_inverted(self):
        return self.inverted

    def get_mappings(self):
        return self.mappings

    def get_mapping(self, idx):
        return self.mappings[idx]

    def set_mapping(self, idx, val):
        self.mappings[idx] = val

    def __iter__(self):
        yield self.get_consequent()

    def is_valid(self):
        return self.antecedent and self.antecedent.is_valid() and self.consequent and self.consequent.is_valid()

    def __str__(self):
        return str(self.antecedent) + ': ' + str(self.consequent)
    
    def __bool__(self):
        return self.is_valid()

    def toJSON(self):
        return {
            'type': 'condition',
            'condition': self.antecedent.toJSON(),
            'body': self.consequent.toJSON(),
            'inverted': self.inverted,
            'persistent': self.persistent,
            'mapping': self.mappings
        }

class Object(object):
    def __init__(self, type_name, name, attributes=None, relation=None, limit=None):
        self.type_name = type_name
        self.name = name

        self.attributes = attributes if attributes else []
        
        self.relation = relation
        self.limit = limit
        
    def get_type_name(self):
        return self.type_name

    def set_type_name(self, value):
        self.type_name = value

    def is_anaphora(self):
        return 'anaphora:it' in self.descriptor

    def toJSON(self):
        return {
            'type': 'object',
            'object_type': self.type_name,
            'descriptor': self.descriptor
        }

    def is_valid(self):
        return self.type_name and self.name

    def __str__(self):
        outstr = '{}:{}'.format(self.type_name, self.name)
        
        if self.attributes:
            outstr += '\n\tattributes:'
        
            for attr in self.attributes:
                for line in str(attr).split('\n'):
                    outstr += '\n\t\t{}'.format(line)

        if self.relation:
            outstr += '\n\trelation:'
            
            for line in str(self.relation).split('\n'):
                outstr += '\n\t\t{}'.format(line)
        
        return outstr
        
    def __bool__(self):
        return self.is_valid()
        
class Attribute(object):
    def __init__(self, type_name, value):
        self.type_name = type_name
        self.value = value

    def toJSON(self):
        return {
            'type': 'attribute',
            'attr_type': self.type_name,
            'value': self.descriptor
        }

    def __str__(self):
        return '[{}={}]'.format(self.type_name, self.value)

class Limit(object):
    pass

class Relation(object):
    def __init__(self, predicate, child):
        self.predicate = predicate
        self.child = child

    def __str__(self):
        return '[{}={}]'.format(self.predicate, str(self.child))

class Anaphora(Object):
    def __init__(self, type_name, name):
        super(Anaphora, self).__init__(type_name, name)

    def __str__(self):
        return 'anophora:it'