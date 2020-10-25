from .parser import *
import copy

import lingua_kb.srv

class State(object):
    def __init__(self):
      self.kb_ask = rospy.ServiceProxy('/kb/ask', lingua_kb.srv.Ask)
      self.kb_assert = rospy.ServiceProxy('/kb/assert', lingua_kb.srv.Assert)
      self.kb_tell = rospy.ServiceProxy('/kb/tell', lingua_kb.srv.Tell)
      self.kb_state = rospy.ServiceProxy('/kb/state', lingua_kb.srv.State)
      
      self.kb_hierarchy = rospy.ServiceProxy('/kb/types/hierarchy', lingua_kb.srv.Hierarchy)
      self.kb_handlers = rospy.ServiceProxy('/kb/handlers/get', lingua_kb.srv.Get)

      self._handlers = None

    def ask(self, fact):
      if Parser.is_query(fact):
        result = Parser.parse(self, fact)
        return result
        
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
            print(statement)
            return not statement or self.ask(statement)
        except NullStatement as e:
            return on_fail

    def snapshot(self):
        return Snapshot(self, self.kb_state().data)

    def copy(self):
      return self.snapshot().copy()

    def difference(self, other):
        return self.snapshot().difference(other)

    def get_hierarchy(self, typename):
      resp = self.kb_hierarchy(typename)
      return (resp.parents, resp.children)

    def poll(self, atom):
      if Parser.is_atom(atom):
        raise Exception('Supplied term is not atomic')
      return self.kb_ask(atom).data

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
  def __init__(self, state, facts):
    super(Snapshot, self).__init__()
    self.__dict__ = state.__dict__
    self.facts = facts
    
    self._cache = []
    
  def ask(self, fact):
    if Parser.is_negative(fact):
      return not self.ask(Parser.negate(fact))

    tokens = Parser.logical_split(fact)

    if self._handlers is None:
      self._handlers = self.kb_handlers().names

    if tokens[0] in self._handlers and fact not in self._cache:
      result = super(Snapshot, self).ask(fact)
      if '?' not in fact:
        self.facts += [ fact ] if result else []
        self._cache.append(fact)

      else:
        for item in result:
          self.facts += [ fact.replace('?', item) ]
          self._cache.append(self.facts[-1])
      

    if '?' not in fact:
      return fact in self.facts

    result = []

    if len(tokens) == 2:
      for item in self.facts:
        result += re.findall('\({} ([^\)]*)\)'.format(tokens[0]), item)
    else:
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
    self.cache(fact)
        
    if Parser.is_negative(fact):
      try:
        self.facts.remove(Parser.negate(fact))
      except ValueError:
        return

    self.facts.append(fact)

  def snapshot(self):
    return self

  def copy(self):
    return copy.deepcopy(self)

  def difference(self, other):
    return set(self.facts).difference(other.snapshot().facts)

  def cache(self, fact):
    if self._handlers is None:
      self._handlers = self.kb_handlers().names

    fact = Parser.negate(fact) if Parser.is_negative(fact) else fact

    tokens = Parser.logical_split(fact)
    
    if tokens[0] in self._handlers and fact not in self._cache:
      self._cache.append(fact)
      return True

    return False

  def __iter__(self):
    for fact in self.facts:
      yield fact

  def __eq__(self, other):
    return set(self.facts) == set(other.snapshot().facts)

  def __str__(self):
      return '\n'.join(sorted(list(self.facts)))