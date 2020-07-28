from .parser import *
import copy

import lingua_kb.srv

class State:
    def __init__(self):
      self.kb_ask = rospy.ServiceProxy('/kb/ask', lingua_kb.srv.Ask)
      self.kb_assert = rospy.ServiceProxy('/kb/assert', lingua_kb.srv.Assert)
      self.kb_tell = rospy.ServiceProxy('/kb/tell', lingua_kb.srv.Tell)
      self.kb_state = rospy.ServiceProxy('/kb/state', lingua_kb.srv.State)

    def ask(self, fact):
        if Parser.is_query(fact):
          return self.kb_ask(fact).data
        
        return self.kb_assert(fact).result

    def update(self, fact):
      self.kb_tell(fact)

    def is_satisfied(self, fact, on_fail = False):
        if Parser.is_negative(fact):
            return not self.is_satisfied(Parser.negate(fact))
        try:
            statement = Parser.parse(self, fact)

            if Parser.is_iterable(statement) or Parser.is_atom(statement):
                return True

            return not statement or self.ask(statement)
        except NullStatement as e:
            return on_fail

    def snapshot(self):
        return Snapshot(self.kb_state().data)

    def copy(self):
      return self.snapshot().copy()

    def difference(self, other):
        return self.snapshot().difference(other)

    def __str__(self):
      return '\n'.join(sorted(list(self.kb.dump())))

    def __eq__(self, other):
      if isinstance(other, self.__class__):
        return self.snapshot() == other.snapshot()
      else:
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class Snapshot(State):
  def __init__(self, facts):
    self.facts = facts

  def ask(self, fact):
    if Parser.is_negative(fact):
      return not self.ask(Parser.negate(fact))

    if '?' not in fact:
      return fact in self.facts
    
    tokens = Parser.logical_split(fact)

    result = []
    if tokens[0] == '?':
      for item in self.facts:
        result += re.findall('\(([^\)]*) {} {}\)'.format(tokens[1], tokens[2]), item)

    elif tokens[1] == '?':
      for item in self.facts:
        result += re.findall('\({} ([^\)]*) {}\)'.format(tokens[0], tokens[2]), item)
      
    elif tokens[2] == '?':
      for item in self.facts:
        result += re.findall('\({} {} ([^\)]*)\)'.format(tokens[0], tokens[1] if tokens[1][0] != '!' else '(?!{})[^\s]*'.format(tokens[1][1:])), item)

    return result
    
  def update(self, fact):
    if Parser.is_negative(fact):
      self.facts.remove(Parser.negate(fact))
    self.facts.append(fact)

  def snapshot(self):
    return self

  def copy(self):
    return copy.deepcopy(self)

  def difference(self, other):
    return set(self.facts).difference(other.snapshot().facts)

  def __iter__(self):
    for fact in self.facts:
      yield fact

  def __eq__(self, other):
    return set(self.facts) == set(other.snapshot().facts)

  def __str__(self):
      return '\n'.join(sorted(list(self.facts)))