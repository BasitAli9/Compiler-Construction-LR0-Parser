# An LR(0) item looks like:  A -> α • β
# The dot shows how far we have read in a production.

class Item:
    def __init__(self, lhs, rhs, dot):
        self.lhs = lhs
        self.rhs = tuple(rhs)
        self.dot = dot

    # symbol right after the dot (None if dot is at the end)
    def next_symbol(self):
        if self.dot < len(self.rhs) and self.rhs != ('e',):
            return self.rhs[self.dot]
        return None

    # return a new item with the dot moved one step forward
    def shift_dot(self):
        return Item(self.lhs, self.rhs, self.dot + 1)

    def __eq__(self, other):
        return (self.lhs, self.rhs, self.dot) == (other.lhs, other.rhs, other.dot)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot))

    def __repr__(self):
        r = list(self.rhs)
        r.insert(self.dot, '•')
        return f"{self.lhs} → {' '.join(r)}"


# Builds the LR(0) automaton (the DFA of item sets).
class LR0Automaton:
    def __init__(self, grammar):
        self.grammar     = grammar
        self.states      = []      # each state is a frozenset of Items
        self.transitions = {}      # (state_index, symbol) -> state_index
        self.build()

    # closure: keep adding items for every non-terminal after a dot
    def closure(self, items):
        result = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for item in result:
                sym = item.next_symbol()
                if sym in self.grammar.non_terminals:
                    for lhs, rhs in self.grammar.productions:
                        if lhs == sym:
                            new_item = Item(lhs, rhs, 0)
                            if new_item not in result:
                                new_items.add(new_item)
                                changed = True
            result |= new_items
        return frozenset(result)

    def build(self):
        # start from the augmented production  S' -> • S
        first_item  = Item(self.grammar.aug_start, self.grammar.productions[0][1], 0)
        start_state = self.closure({first_item})
        self.states = [start_state]
        queue = [0]

        while queue:
            state_idx = queue.pop(0)
            state = self.states[state_idx]

            # find all symbols that appear right after a dot
            symbols = {item.next_symbol() for item in state if item.next_symbol()}

            for sym in symbols:
                # advance all items that have this symbol after their dot
                moved = {item.shift_dot() for item in state if item.next_symbol() == sym}
                next_state = self.closure(moved)

                if next_state not in self.states:
                    self.states.append(next_state)
                    queue.append(len(self.states) - 1)

                self.transitions[(state_idx, sym)] = self.states.index(next_state)


# Builds the ACTION and GOTO tables for LR(0) parsing.
# LR(0) does not use lookahead — it reduces in a state if
# ANY item in that state is complete.
class LR0Table:
    def __init__(self, grammar, automaton):
        self.grammar    = grammar
        self.automaton  = automaton
        self.action     = {}   # (state, terminal) -> 'sN' | 'rN' | 'acc'
        self.goto_table = {}   # (state, non-terminal) -> state
        self.conflicts  = []   # list of conflict descriptions (for reporting)
        self.build()

    def set_action(self, state, symbol, value):
        key = (state, symbol)
        if key in self.action and self.action[key] != value:
            self.conflicts.append(
                f"Conflict at state {state}, symbol '{symbol}': "
                f"{self.action[key]} vs {value}"
            )
        else:
            self.action[key] = value

    def build(self):
        g    = self.grammar
        auto = self.automaton

        # shifts and gotos come from the transitions
        for (state, sym), next_state in auto.transitions.items():
            if sym in g.terminals:
                self.set_action(state, sym, f"s{next_state}")
            elif sym in g.non_terminals:
                self.goto_table[(state, sym)] = next_state

        # reduces (and accept) come from completed items
        for state_idx, state in enumerate(auto.states):
            for item in state:
                is_complete = (item.dot == len(item.rhs)) or (item.rhs == ('e',))
                if is_complete:
                    if item.lhs == g.aug_start:
                        self.set_action(state_idx, '$', 'acc')
                    else:
                        prod_idx = g.productions.index((item.lhs, list(item.rhs)))
                        # LR(0): reduce on ALL terminals (no lookahead check)
                        for terminal in g.terminals | {'$'}:
                            self.set_action(state_idx, terminal, f"r{prod_idx}")
