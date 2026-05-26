from collections import defaultdict


# This class stores a grammar and parses it from plain text input.
# Format:  E -> E + T | T
# Epsilon is written as 'e' or 'eps'
#
# Each space-separated token in the RHS is ONE atomic symbol for the dot.
# So  E -> E + T  has three symbols: E, +, T — the dot steps over them one
# at a time, giving the single-token step-through the user expects.
class Grammar:
    def __init__(self):
        self.productions   = []
        self.terminals     = set()
        self.non_terminals = set()
        self.start_symbol  = None
        self.aug_start     = None   # augmented start like S'

    def load(self, text):
        self.productions   = []
        self.terminals     = set()
        self.non_terminals = set()
        self.start_symbol  = None

        lines = [l.strip() for l in text.strip().split('\n') if '->' in l]
        if not lines:
            raise ValueError("No valid rules found. Use format: A -> B C | D")

        for line in lines:
            lhs, rhs_part = line.split('->', 1)
            lhs = lhs.strip()
            if not lhs:
                continue
            if self.start_symbol is None:
                self.start_symbol = lhs
            self.non_terminals.add(lhs)

            for alt in rhs_part.split('|'):
                # Each whitespace-separated token = one atomic symbol.
                # The dot advances exactly one token per step.
                #E -> T | E + T to ['E', '+', 'T']
                symbols = alt.strip().split()
                if not symbols or symbols in (['e'], ['eps']):
                    self.productions.append((lhs, ['e']))
                else:
                    self.productions.append((lhs, symbols))

        # anything not a non-terminal is a terminal
        for lhs, rhs in self.productions:
            for sym in rhs:
                if sym not in self.non_terminals and sym not in ('e', 'eps'):
                    self.terminals.add(sym)

        # add augmented rule  S' -> S  at the front
        self.aug_start = self.start_symbol + "'"
        self.productions.insert(0, (self.aug_start, [self.start_symbol]))
        self.non_terminals.add(self.aug_start)


# Computes FIRST and FOLLOW sets for all non-terminals in a grammar.
class FirstFollow:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first   = defaultdict(set)
        self.follow  = defaultdict(set)
        self.compute()

    def compute(self):
        g = self.grammar

        # FIRST of a terminal is itself like + or*
        for t in g.terminals:
            self.first[t] = {t}

        # keep updating FIRST sets until nothing changes
        changed = True
        while changed:
            changed = False
            for lhs, rhs in g.productions:
                old_size = len(self.first[lhs])
                if rhs == ['e']:
                    self.first[lhs].add('ε')
                else:
                    for sym in rhs:
                        self.first[lhs] |= self.first.get(sym, set()) - {'ε'}
                        if 'ε' not in self.first.get(sym, set()):
                            break
                    else:
                        self.first[lhs].add('ε')
                if len(self.first[lhs]) != old_size:
                    changed = True

        # FOLLOW of the augmented start always contains $
        self.follow[g.aug_start].add('$')

        changed = True
        while changed:
            changed = False
            for lhs, rhs in g.productions:
                for i, sym in enumerate(rhs):
                    if sym in g.non_terminals:
                        old_size = len(self.follow[sym])
                        rest = rhs[i + 1:]
                        result = set()
                        for s in rest:
                            result |= self.first.get(s, set()) - {'ε'}
                            if 'ε' not in self.first.get(s, set()):
                                break
                        else:
                            result.add('ε')
                        self.follow[sym] |= result - {'ε'}
                        if 'ε' in result:
                            self.follow[sym] |= self.follow[lhs]
                        if len(self.follow[sym]) != old_size:
                            changed = True
