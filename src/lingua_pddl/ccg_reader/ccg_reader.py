import itertools
import re
import xml.etree.ElementTree as ET
from .types import Task, Conditional, Conjunction, Object, Attribute, Limit, Relation, Anaphora

class CCGReader:
    @staticmethod
    def read(text):
        return XMLReader.read(ET.fromstring(text))

class XMLReader: 
    @staticmethod
    def read(node):
        try:
            if node.tag == 'xml':
                return XMLReader.read(node.find('lf')[0])
            
            if TaskReader.is_task(node):
                return TaskReader.read(node)

            if ConditionalReader.is_conditional(node):
                return ConditionalReader.read(node)

            if ConjunctionReader.is_conjunction(node):
                return ConjunctionReader.read(node)

            if QueryReader.is_query(node):
                return QueryReader.read(node)

            if PerceptReader.is_percept(node):
                return PerceptReader.read(node)
            
            return ObjectReader.read(node)
        except Exception as e:
            # print(str(e))
            pass


        return None

class AttributeReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node)

        return Attribute(AttributeReader.get_type(node), AttributeReader.get_value(node))

    @staticmethod
    def get_type(node):
        return node.find('nom').get('name').split(':')[1]

    @staticmethod
    def get_value(node):
        return node.find('prop').get('name')

    @staticmethod
    def is_attribute(node):
        try:
            if node.tag == 'satop':
                return ':adj' in node.get('nom')
            return ':adj' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False

class RelationReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node)

        return Relation(RelationReader.get_type(node), ObjectReader.read(node))

    @staticmethod
    def get_type(node):
        for child in node.findall('diamond'):
            if child.get('mode') == 'predicate':
                return child.find('prop').get('name')
        return None

    @staticmethod
    def get_value(node):
        return node.find('prop').get('name')

class ObjectReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node)

        return ObjectReader.get_object(node)

    @staticmethod
    def get_type_name(node):
        if node.tag == 'satop':
            return node.get('nom').split(':')[1]
        return node.find('nom').get('name').split(':')[1]

    @staticmethod
    def get_object(node):
        if ObjectReader.is_anaphora(node):
            return Anaphora(
                ObjectReader.get_type_name(node),
                ObjectReader.get_name(node),
            )

        return Object(
            ObjectReader.get_type_name(node),
            ObjectReader.get_name(node),
            ObjectReader.get_attributes(node),
            ObjectReader.get_relation(node),
            ObjectReader.get_limit(node)
        )
        # components = []

        # if not ObjectReader.is_universal(node):
        #     components.append(ObjectReader.get_object_property(node, ObjectReader.is_relation(node)))

        # for arg in node.findall('diamond'):
        #     if arg.get('mode').startswith('Compound'):
        #         continue

        #     component = ObjectReader.get_object_property(arg, ObjectReader.is_relation(arg))
        #     if component:
        #         components.append(component)
        # print(components)
        # if len(components) > 1:
        #     result = '(intersect ' + ' '.join(components) + ')'
        # else:
        #     result = components[0]

        # return ObjectReader.get_limit(node, result)

    @staticmethod
    def get_name(node):
        return node.find('prop').get('name')

    @staticmethod
    def get_attributes(node):
        attributes = []

        for child in node.findall('diamond'):
            if child.get('mode') == 'mod':
                attributes.append(AttributeReader.read(child))

        return attributes

    @staticmethod
    def is_anaphora(node):
        return node.find('prop') is not None and node.find('prop').get('name') in ['it']

    @staticmethod
    def get_relation(node):
        for child in node.findall('diamond'):
            if child.get('mode') == 'relation':
                return RelationReader.read(child)
        return None

    @staticmethod
    def get_limit(node):
        return None

class TaskReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node.find('lf')[0])

        arguments = TaskReader.get_method_args(node)

        return Task(TaskReader.get_method_name(node, arguments),
                    {'arg' + str(idx) : argument for idx, argument in enumerate(arguments)})


    @staticmethod
    def get_method_name(node, arguments):
        task_name = node.find('prop').get('name')
        type_names = []

        for diamond in node.findall('diamond'):
            if not diamond.get('mode').startswith('particle'):
                continue

            task_name = task_name + '_' + diamond.find('prop').get('name')


        for argument in arguments:
            type_names.append(argument.get_type_name())

        return task_name + '(' + ', '.join([type_name + ' arg' + str(idx)
                                             for idx, type_name in enumerate(type_names)]) + ')'

    @staticmethod
    def get_method_args(node, layer = 0):
        children = [child for child in node.findall('diamond') if child.get('mode').startswith('arg')]
        args = []
        for child in children:
            args.append(XMLReader.read(child))

        return args

    @staticmethod
    def is_task(node):
        try:
            if node.tag == 'satop':
                return ':action' in node.get('nom')
            return ':action' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False

class ConditionalReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node.find('lf')[0])

        antecedent = ConditionalReader.get_antecedent(node)
        consequent = ConditionalReader.get_consequent(node)

        return Conditional(XMLReader.read(antecedent), XMLReader.read(consequent), ConditionalReader.is_persistent(node), ConditionalReader.is_inverted(node))

    @staticmethod
    def is_conditional(node):
        try:
            if node.tag == 'satop':
                return ':condition' in node.get('nom')
            return ':condition' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False

    @staticmethod
    def get_antecedent(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Antecedent'][0]

    @staticmethod
    def get_consequent(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Consequent'][0]

    @staticmethod
    def is_persistent(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'persistent'][0].find('prop').get('name') == 'true'

    @staticmethod
    def is_inverted(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'inverted'][0].find('prop').get('name') == 'true'

class ConjunctionReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node.find('lf')[0])

        first = ConjunctionReader.get_first_arg(node)
        second = ConjunctionReader.get_second_arg(node)

        return Conjunction(ConjunctionReader.get_tag(node), XMLReader.read(first), XMLReader.read(second))

    @staticmethod
    def get_tag(node):
        return node.find('prop').get('name')

    @staticmethod
    def get_first_arg(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'left'][0]

    @staticmethod
    def get_second_arg(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'right'][0]

    @staticmethod
    def is_conjunction(node):
        try:
            if node.tag == 'satop':
                return ':conjunction' in node.get('nom')
            return ':conjunction' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False

class QueryReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return XMLReader.read(node.find('lf')[0])

        return Query(QueryReader.get_predicate(node), XMLReader.read(QueryReader.get_descriptor(node)))

    @staticmethod
    def get_predicate(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'arg0'][0].find('prop').get('name')

    @staticmethod
    def get_descriptor(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'arg1'][0]

    @staticmethod
    def is_query(node):
        try:
            if node.tag == 'satop':
                return ':query' in node.get('nom')
            return ':query' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False

class PerceptReader:
    @staticmethod
    def read(node):
        try:
            if node.tag == 'xml':
                return XMLReader.read(node)

            children = node.findall('diamond')
            child = [child for child in children if child.get('mode') == 'arg0'][0]
            return XMLReader.read(child)
        except Exception as e:
           print(str(e))

        return None

    @staticmethod
    def is_percept(node):
        try:
            if node.tag == 'satop':
                return ':percept' in node.get('nom')
            return ':percept' in node.find('nom').get('name')
        except Exception as e:
            print(str(e))
        return False
            