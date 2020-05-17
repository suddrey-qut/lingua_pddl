import itertools
import re
import xml.etree.ElementTree as ET
from .types import Task, Conditional, Conjunction, Object

class CCGReader:
    @staticmethod
    def parse(text):
      return CCGReader.read(ET.fromstring(text))
      
    @staticmethod
    def read(node):
        try:
            if node.tag == 'xml':
                return CCGReader.read(node.find('lf')[0])

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
            pass


        return None

class ObjectReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return CCGReader.read(node)

        return Object(ObjectReader.get_type_name(node), ObjectReader.get_object(node))

    @staticmethod
    def get_type_name(node):
        if node.tag == 'satop':
            return node.get('nom').split(':')[1]
        return node.find('nom').get('name').split(':')[1]

    @staticmethod
    def get_object(node):
        components = []

        if not ObjectReader.is_universal(node):
            components.append(ObjectReader.get_object_property(node, ObjectReader.is_relation(node)))

        for arg in node.findall('diamond'):
            if arg.get('mode').startswith('Compound'):
                continue

            component = ObjectReader.get_object_property(arg, ObjectReader.is_relation(arg))
            if component:
                components.append(component)

        if len(components) > 1:
            result = '(intersect ' + ' '.join(components) + ')'
        else:
            result = components[0]

        return ObjectReader.get_limit(node, result)

    @staticmethod
    def get_object_property(node, is_relation = False):

        if ObjectReader.is_anaphora(node):
            return 'anaphora:' + node.find('prop').get('name')

        nominal = node.find('nom')

        if nominal is None:
            return None

        if is_relation:
            child = node.find('diamond')

            if child is not None:
                return '(is_' + node.find('prop').get('name') + ' ' + ObjectReader.get_object_property(child, ObjectReader.is_relation(child)) + ' ?)'
            else:
                return '(is_' + node.find('nom').get('name').split(':')[1] + ' ' + node.find('prop').get('name') + ' ?)'

        property_name = ObjectReader.get_property_name(node)

        return '(' + property_name + ' ?)'

    @staticmethod
    def get_property_name(node, property_name=''):
        if not property_name:
            property_name = node.find('prop').get('name')

        for diamond in node.findall('diamond'):
            if not diamond.get('mode').startswith('Compound'):
                continue

            property_name = property_name + '_' + diamond.find('prop').get('name')
            property_name = ObjectReader.get_property_name(diamond, property_name)

        return property_name

    @staticmethod
    def is_anaphora(node):
        return node.find('prop') is not None and node.find('prop').get('name') in ['it']

    @staticmethod
    def is_relation(node):
        return node.get('mode') == 'Mod'

    @staticmethod
    def is_universal(node):
        try:
            return [child for child in node.findall('diamond')
                          if child.get('mode') == 'num'][0].find('prop').get('name') == 'all'
        except:
            return False

    @staticmethod
    def get_limit(node, condition):
        number = None
        word = None

        for arg in [child for child in node.findall('diamond') if child.get('mode') in ['det', 'num']]:
            if arg.get('mode') == 'det':
                word = arg.find('prop').get('name')
            if arg.get('mode') == 'num':
                number = arg.find('prop').get('name')

        if not word or not number:
            return condition

        if number == 'pl':
            return condition

        return '(' + ('only' if word != 'a' else 'any') + ' ' + condition + ' 1)'

class TaskReader:
    @staticmethod
    def read(node):
        if node.tag == 'xml':
            return CCGReader.read(node.find('lf')[0])

        arguments = TaskReader.get_method_args(node)

        return Task(TaskReader.get_method_name(node, arguments),
                    {'arg' + str(idx) : argument for idx, argument in enumerate(arguments)})


    @staticmethod
    def get_method_name(node, arguments):
        task_name = node.find('prop').get('name')
        type_names = []

        for diamond in node.findall('diamond'):
            if not diamond.get('mode').startswith('Relation'):
                continue

            task_name = task_name + '_' + diamond.find('prop').get('name')


        for argument in arguments:
            type_names.append(argument.get_type_name())

        return task_name + '(' + ', '.join([type_name + ' arg' + str(idx)
                                             for idx, type_name in enumerate(type_names)]) + ')'

    @staticmethod
    def get_method_args(node, layer = 0):
        children = [child for child in node.findall('diamond') if child.get('mode').startswith('Arg')]
        args = []
        for child in children:
            args.append(CCGReader.read(child))

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
            return CCGReader.read(node.find('lf')[0])

        antecedent = ConditionalReader.get_antecedent(node)
        consequent = ConditionalReader.get_consequent(node)

        return Conditional(CCGReader.read(antecedent), CCGReader.read(consequent), ConditionalReader.is_persistent(node), ConditionalReader.is_inverted(node))

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
            return CCGReader.read(node.find('lf')[0])

        first = ConjunctionReader.get_first_arg(node)
        second = ConjunctionReader.get_second_arg(node)

        return Conjunction(ConjunctionReader.get_tag(node), CCGReader.read(first), CCGReader.read(second))

    @staticmethod
    def get_tag(node):
        return node.find('prop').get('name')

    @staticmethod
    def get_first_arg(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Arg0'][0]

    @staticmethod
    def get_second_arg(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Arg1'][0]

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
            return CCGReader.read(node.find('lf')[0])

        return Query(QueryReader.get_predicate(node), CCGReader.read(QueryReader.get_descriptor(node)))

    @staticmethod
    def get_predicate(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Arg0'][0].find('prop').get('name')

    @staticmethod
    def get_descriptor(node):
        children = node.findall('diamond')
        return [child for child in children if child.get('mode') == 'Arg1'][0]

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
                return CCGReader.read(node)

            children = node.findall('diamond')
            child = [child for child in children if child.get('mode') == 'Arg0'][0]
            return CCGReader.read(child)
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

if __name__ == '__main__':
    from _openccg import OpenCCG

    with OpenCCG() as openccg:

        text = 'dance'
        parses = openccg.parse(text)

        for parse in parses:

            print(ET.tostring(parse))
            task = CCGReader.read(parse)

            if not task:
                continue

            print(task.toJSON())