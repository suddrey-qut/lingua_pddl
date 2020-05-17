import re
import copy

class Task:
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

    def __str__(self):
        return self.get_name() + ' - {' + ' '.join([key + ': ' + str(self.method_arguments[key]) for key in self.method_arguments]) + '}'

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

class Conjunction:
    def __init__(self, tag, first, second):
        self.tag = tag
        self.first = first
        self.second = second

        self.id = None

    def get_type_name(self):
        if isinstance(self.first, Object):
            return self.first.get_type_name()
        return None

    def get_descriptor(self):
        return str(self)

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def ground(self, state):
        if not self.first.is_grounded():
            self.first.ground(state)

        if not self.second.is_grounded():
            self.second.ground(state)

        self.set_id(parse(state, '({0} {1} {2})'.format(self.tag,
                                                        self.first.get_id(),
                                                        self.second.get_id())))

    def is_grounded(self):
        return self.id is not None

    def get_first(self):
        return self.first

    def set_first(self, first):
        self.first = first

    def get_second(self):
        return self.second

    def set_second(self, second):
        self.second = second

    def __iter__(self):
        if not isinstance(self.first, Conjunction):
            yield self.first
        else:
            for item in self.first:
                yield item
        if not isinstance(self.second, Conjunction):
            yield self.second
        else:
            for item in self.second:
                yield item

    def __str__(self):
        return '({0} {1} {2})'.format(self.tag, str(self.first), str(self.second))


    def toJSON(self):
        return [item.toJSON() for item in self]

class Conditional:
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

    def __str__(self):
        return str(self.antecedent) + ': ' + str(self.consequent)
    
    def toJSON(self):
        return {
            'type': 'condition',
            'condition': self.antecedent.toJSON(),
            'body': self.consequent.toJSON(),
            'inverted': self.inverted,
            'persistent': self.persistent,
            'mapping': self.mappings
        }

class Object:
    def __init__(self, type_name, descriptor = ''):
        self.descriptor = descriptor
        self.type_name = type_name

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