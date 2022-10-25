#!/usr/bin/env python3

from __future__ import annotations
from typing import Callable, Optional
from string import ascii_uppercase

OR = "∨"
AND = "∧"
NOT = "¬"
IMPLIES = "⇒"
EQUIVALENT = "⇔"

operator_macros = {
        "or": OR,
        "and": AND,
        "not ": NOT, # Removes space after 'not'
        "not": NOT, # In case 'not' is not followed by a space
        "eq": EQUIVALENT,
        "<=>": EQUIVALENT,
        "impl": IMPLIES,
        "=>": IMPLIES,
}

class Statement:
    def __init__(self, func: Callable, description: str):
        self.func = func
        self._description = description
        self._formatted: Optional[str] = None

    def evaluate(self, *args) -> bool:
        assert all(isinstance(arg, bool) for arg in args)
        return self.func(*args)

    __call__ = evaluate

    def format(self):
        if self._formatted is None:
            self._formatted = self._do_format()
        return self._formatted

    def _do_format(self) -> str:
        f = self._description
        for macro, subst in operator_macros.items():
            f = f.replace(macro, subst)
        return f

def implication(a: bool, b: bool) -> bool:
    if a:
        return b
    else:
        return True

def equivalence(a: bool, b: bool) -> bool:
    return a == b

def format_bool(a: bool) -> str:
    return a and "T" or "F"

def format_table(table: list[list[str]], delim: str = "   ") -> str:
    col_widths = [max([len(table[row][col]) for row in range(len(table))])
        for col in range(len(table[0]))]
    out = ""
    for i, row in enumerate(table):
        out += delim.join([el.ljust(col_widths[j]) for j, el in enumerate(row)])
        out += "\n" * (i != len(table) - 1)
        
    return out

def main():
    n_args = 3
    assert n_args <= 26
    args = [False for _ in range(n_args)]

    s1 = Statement(lambda a, b, c: equivalence(a, b) and equivalence(b, c), "(A <=> B) and (B <=> C)")
    s2 = Statement(lambda a, b, c: equivalence(a, c), "A <=> C")
    s3 = Statement(lambda a, b, c: implication(equivalence(a, b) and equivalence(b, c), equivalence(a, c)), "(A <=> B) and (B <=> C) => (A <=> C)")

    table = []
    table.append([*ascii_uppercase[:n_args], s1.format(), s2.format(), s3.format()])
    for i in range(2 ** n_args):
        args = [not((i >> j) % 2) for j in reversed(range(n_args))]
        table.append(list(map(format_bool, [*args, s1(*args), s2(*args), s3(*args)])))

    print(format_table(table))

if __name__ == "__main__":
    main()

