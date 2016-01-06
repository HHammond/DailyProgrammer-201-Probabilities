from __future__ import print_function
# Convert raw_input to input for python3 compatibility
try:
    input = raw_input
except NameError:
    pass

from collections import defaultdict
from itertools import chain, combinations, groupby


class Variable(object):

    __slots__ = ['token', 'negation']

    def __init__(self, token, negation=False):
        self.token = token
        self.negation = negation

    def __invert__(self):
        return Variable(self.token, not self.negation)

    def __str__(self):
        if self.negation:
            return "!{}".format(self.token)
        return self.token

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, Variable):
            return hash(self) == hash(other)

    def is_exclusion(self):
        return self.negation


class Statement(object):

    def __init__(self, variables):
        self.variables = frozenset(variables)

    def __contains__(self, other):
        if isinstance(other, Statement):
            return all(e in other for e in self)
        if isinstance(other, Variable):
            return other in self.variables
        raise TypeError()

    def is_valid(self):
        return all(~e not in self for e in self)

    def __str__(self):
        return "P({})".format(", ".join(str(v) for v in self.variables))

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.variables)

    def __hash__(self):
        return hash(self.variables)

    def __eq__(self, other):
        return self.variables == other.variables

    def __ne__(self, other):
        return not self == other


def powerset(iterable, minimum=1):
    s = list(iterable)
    c = chain.from_iterable(combinations(s, r)
                            for r in range(minimum, len(s)+1))
    return c


def solve(symbols, input_data, to_solve):
    # Record known variable values
    known = {}
    for s, value in input_data:
        known[Statement(s)] = value

    print("Known Probabilities:")
    print("-" * 40)
    for k, v in known.items():
        print(" ", k, "=", v)
    print("-" * 40)

    # Build lists of symbols
    all_symbols = symbols + [~s for s in symbols]

    # Convert to_solve into Statement
    to_solve = Statement(to_solve)

    # Create list of all valid statements
    all_statements = (Statement(v) for v in powerset(all_symbols))
    all_statements = [v for v in all_statements if v.is_valid()]

    # Create structure of subset heirarchy
    children = defaultdict(set)
    for x, y in combinations(all_statements, r=2):
        if x != y:
            if x in y:
                children[y].add(x)
            if y in x:
                children[x].add(y)
    # Make sure all keys are in children dict
    for s in all_statements:
        children[s] = children[s]

    print("Steps:")
    print("-" * 40)
    # Try solving things until we've tried everything and failed
    has_changed = True
    while has_changed:
        has_changed = False

        # Update known values with inverses of known variables
        updates = {}
        for statement in known:
            if len(statement.variables) == 1:
                inverted_symbol = ~list(statement.variables)[0]
                s = Statement([inverted_symbol])

                if s not in known:
                    updates[s] = 1-known[statement]
                    has_changed = True
                    print("Solved by inverse", s, "=", 1 - known[statement])
        known.update(updates)

        # Iterate from largest statements to smallest
        # Bottom up approach makes solving subsets require fewer iterations
        for parent in reversed(all_statements):

            # Iterate over subset hierarchy filling in unknowns from bottom up
            key = lambda s: len(s.variables)
            subsets = sorted(children[parent], key=key)
            for length, group in groupby(subsets, key=key):

                # Group subsets by the variables they span
                spans = defaultdict(list)
                for g in group:
                    span = frozenset(s if not s.is_exclusion() else ~s
                                     for s in g)
                    spans[span].append(g)

                # Iterate over known spans and solve
                # We know that all spans union to parent
                for span in spans.values():
                    unknowns = [expr for expr in span if expr not in known]

                    # Solve unknown subset if others are known
                    if parent in known and len(unknowns) == 1:
                        unknown = unknowns[0]
                        total = sum(known[expr]
                                    for expr in span if expr != unknown)
                        known[unknown] = known[parent] - total
                        has_changed = True
                        print("Solved by difference:", unknown, "=", known[unknown])
                        for e in span+[parent]:
                            if e == unknown:
                                continue
                            print("|",e, "=", known.get(e))
                        print("=>", unknown, "=", known[unknown])

                    # Solve for parent if subsets are known
                    if parent not in known and not unknowns:
                        total = sum(known[expr] for expr in span)
                        known[parent] = total
                        has_changed = True
                        print("Solved by union:", parent, "=", total)
                        for e in span+[parent]:
                            if e == parent:
                                continue
                            print("|", e, "=", known[e])
                        print("=>", parent, "=", known[parent])
    print("-" * 40)
    print("Known:")
    print("-" * 40)

    for s in all_statements:
        print(s, "=", known.get(s, "?"))
        # for c in children[s]:
        #     print(" ", c, "=", known.get(c, "?"))

    print("-" * 40)
    print("Solution:")
    print("-" * 40)
    print(to_solve, "=", known.get(to_solve, "Not enough information"))


def process_input():
    n, symbols = input().split(None, 1)
    n = int(n)
    symbols = [Variable(s) for s in symbols.split()]

    read_line = lambda: input().replace(':', '').split()

    input_data = []
    for _ in range(n):
        input_data.append(process_input_row(read_line()))

    to_solve = process_input_row(read_line(), final_line=True)
    return symbols, input_data, to_solve


def process_input_row(row, final_line=False):
    parse_symbols = lambda data: {Variable(s) for s in data if s != '&'}

    if not final_line:
        value = float(row[-1])
        symbols = parse_symbols(row[:-1])
        return frozenset(symbols), value
    else:
        symbols = parse_symbols(row)
        return frozenset(symbols)

if __name__ == "__main__":
    symbols, input_data, to_solve = process_input()
    solve(symbols, input_data, to_solve)
    symbols
