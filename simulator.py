# Runs the LR(0) parsing algorithm step by step.
# Returns a list of steps (the trace) and True/False for accepted/rejected.

class LR0Simulator:
    def __init__(self, grammar, table):
        self.grammar = grammar
        self.table   = table

    def simulate(self, tokens):
        tokens    = tokens + ['$']   # add end-of-input marker
        stack     = [0]              # state stack
        sym_stack = ['$']            # symbol stack (just for display)
        pos       = 0                # current position in tokens
        trace     = []

        while True:
            state     = stack[-1]
            lookahead = tokens[pos]
            action    = self.table.action.get((state, lookahead))

            # record current step before doing anything
            trace.append({
                'stack'  : str(stack),
                'symbols': ' '.join(sym_stack),
                'input'  : ' '.join(tokens[pos:]),
                'action' : str(action) if action else 'REJECT'
            })

            if action == 'acc':
                return trace, True

            if action is None:
                return trace, False

            # shift: push next state and consume token
            if action.startswith('s'):
                next_state = int(action[1:])
                stack.append(next_state)
                sym_stack.append(lookahead)
                pos += 1

            # reduce: pop |rhs| items and push goto state
            elif action.startswith('r'):
                prod_idx      = int(action[1:])
                lhs, rhs      = self.grammar.productions[prod_idx]

                if rhs != ['e']:
                    for _ in rhs:
                        stack.pop()
                        sym_stack.pop()

                sym_stack.append(lhs)

                goto_state = self.table.goto_table.get((stack[-1], lhs))
                if goto_state is None:
                    return trace, False
                stack.append(goto_state)
