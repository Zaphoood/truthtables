#!/usr/bin/env python3

from __future__ import annotations
from enum import Enum, auto
from typing import Optional
from string import ascii_uppercase

class Operator(Enum):
    NONE = auto()
    NOT = auto()
    OR = auto()
    AND = auto()
    IMPLIES = auto()
    EQUIVALENT = auto()

operators_as_strs = {
    Operator.OR: "∨",
    Operator.AND: "∧",
    Operator.NOT: "¬",
    Operator.IMPLIES: "⇒",
    Operator.EQUIVALENT: "⇔"
}

operator_macros = {
        "or":   Operator.OR,
        "and":  Operator.AND,
        "not":  Operator.NOT, # Removes space after 'not'
        "not":  Operator.NOT, # In case 'not' is not followed by a space
        "eq":   Operator.EQUIVALENT,
        "<=>":  Operator.EQUIVALENT,
        "impl": Operator.IMPLIES,
        "=>":   Operator.IMPLIES,
}


class Statement:
    """Represent a logical statement that can be formatted nicely and whose value can be evaluated
    by providing values for its variables.

    A logical statement is represented by a binary tree with Statements as nodes, where each nodes left and right
    child are the respective sub-statements. For example, the statement "¬A ∨ B" is represented as:

           or
         /    \
      not A    B

    Note that Statements that have unary operators or no operator at all (such as "B" in the above example) have no right child.
    """

    def __init__(self, literal: str):
        self.literal = literal
        self.operator: Operator
        self.left: Optional[Statement]
        self.right: Statement
        self._formatted: Optional[str] = None

        self.operator, self.left, self.right = self._parse_statement(literal)

    def evaluate(self, var_table: dict[str, bool]) -> bool:
        match self.operator:
            case Operator.NONE:
                return self.right.evaluate(var_table)
            case Operator.NOT:
                return not self.right.evaluate(var_table)
            case Operator.OR:
                assert isinstance(self.left, Statement)
                return self.left.evaluate(var_table) or self.right.evaluate(var_table)
            case Operator.AND:
                assert isinstance(self.left, Statement)
                return self.left.evaluate(var_table) and self.right.evaluate(var_table)
            case Operator.IMPLIES:
                assert isinstance(self.left, Statement)
                return implication(self.left.evaluate(var_table), self.right.evaluate(var_table))
            case Operator.EQUIVALENT:
                assert isinstance(self.left, Statement)
                return equivalence(self.left.evaluate(var_table), self.right.evaluate(var_table))
            case _:
                raise Exception("Exhaustive handling of Operators")

    __call__ = evaluate

    def _parse_statement(self, literal: str) -> tuple[Operator, Optional[Statement], Statement]:
        """Returns a callable representing the literal expression
        and an integer representing the number of arguments.

        Parantheses are allowed, other types of brackets are not.
        All tokens of the expression (including parentheses) must be separated by spaces."""
        literal = literal.strip()
        if self._is_valid_var_name(literal):
            return Operator.NONE, None, Variable(literal)
        tokens = literal.split(" ")
        # TODO: Find all variable names

        return self._parse_substatement(tokens)

    def _parse_substatement(self, tokens: list[str]) -> tuple[Operator, Optional[Statement], Statement]:
        parenthesis_level = 0

        acc: list[str] = []
        left: list[str] = []
        right: list[str] = []
        op: Optional[Operator] = None
        for t in tokens:
            if t == "(":
                acc += t
                parenthesis_level += 1
                continue
            elif t ==  ")":
                parenthesis_level -= 1
                acc += t
                continue

            if parenthesis_level == 0:
                if self._is_valid_var_name(t):
                    acc.append(t)
                    continue
                elif t in operator_macros:
                    if not left:
                        left = acc
                        acc = []
                    op = operator_macros[t]
                    continue
                else:
                    raise SyntaxError(f"'{t}' is not a valid token.")
            else:
                acc.append(t)

        right = acc

        if left:
            if left[0] == "(":
                left = left[1:]
            if left[-1] == ")":
                left = left[:-1]
        if right:
            if right[0] == "(":
                right = right[1:]
            if right[-1] == ")":
                right = right[:-1]
        if not op:
            if len(left) == 0:
                op = op or Operator.NONE
                l = None
            else:
                raise Exception(f"No operator in expression but right operand: {tokens}")
        else:
            l = Statement(" ".join(left))
        r = Statement(" ".join(right))
        return op, l, r

    def _is_valid_var_name(self, name_candidate: str) -> bool:
        # TODO: Consider extending the definition of a valid variable name
        return name_candidate in ascii_uppercase

    def format(self):
        if self._formatted is None:
            self._formatted = self._do_format()
        return self._formatted

    def _do_format(self) -> str:
        f = self.literal
        for macro, subst in operator_macros.items():
            f = f.replace(macro, operators_as_strs[subst])
        return f

class Variable(Statement):
    def __init__(self, name: str):
        self.name = name

    def evaluate(self, var_table: dict[str, bool]) -> bool:
        return var_table[self.name]

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
    variables = ["A", "B"]
    var_table = {var: False for var in variables}

    statements = [
        Statement("A or B"),
        Statement("A and B"),
        Statement("A => B"),
        Statement("A <=> B")
    ]

    table = []
    table.append([*ascii_uppercase[:len(variables)], *[s.format() for s in statements]])

    for i in range(2 ** len(variables)):
        for j, var in enumerate(reversed(variables)):
            var_table[var] = not((i >> j) % 2)
        table.append([])
        table[-1].extend((map(format_bool,
            [var_table[v] for v in variables])))
        table[-1].extend((map(format_bool,
            [s(var_table) for s in statements])))

    print(format_table(table))

if __name__ == "__main__":
    main()

