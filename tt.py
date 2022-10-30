#!/usr/bin/env python3

from __future__ import annotations
from enum import IntEnum, auto
from typing import Optional
from string import ascii_uppercase

class AmbiguousPrecedence(Exception):
    def __init__(self, expression: Optional[str] = None):
        message = "Precedence is not defined between implication (=>) and equivalence (<=>). Please use parentheses to clarify your statement."
        if expression:
            super().__init__(message + f" In expression:\n{expression}")
        else:
            super().__init__(message)

# Ordered by precedence (highest to lowest)
class Operator(IntEnum):
    NONE = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    EQUIVALENT = auto()

operators_as_strs = {
    Operator.NOT: "¬",
    Operator.AND: "∧",
    Operator.OR: "∨",
    Operator.IMPLIES: "⇒",
    Operator.EQUIVALENT: "⇔"
}

operator_macros = {
        "not":  Operator.NOT,
        "and":  Operator.AND,
        "or":   Operator.OR,
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

    def _parse_statement(self, literal: str) -> tuple[Operator, Optional[Statement], Statement]:
        """Returns a callable representing the literal expression
        and an integer representing the number of arguments.

        Parantheses are allowed, other types of brackets are not.
        All tokens of the expression (including parentheses) must be separated by spaces."""
        literal = literal.strip()
        if self._is_valid_var_name(literal):
            return Operator.NONE, None, Variable(literal)
        tokens = self._split_tokens(literal)
        # TODO: Find all variable names

        try:
            tokens = self._parse_substatement(tokens)
        except AmbiguousPrecedence as e:
            raise AmbiguousPrecedence(literal)

        return tokens

    def _split_tokens(self, literal: str) -> list[str]:
        tokens = []
        acc = ""
        for c in literal:
            if c in [" ", "(", ")"]:
                if acc:
                    tokens.append(acc)
                    acc = ""
                if c != " ":
                    tokens.append(c)
            else:
                acc += c
        if acc:
            tokens.append(acc)

        return tokens

    def _parse_substatement(self, tokens: list[str]) -> tuple[Operator, Optional[Statement], Statement]:
        left: list[str] = []
        right: list[str] = []
        op: Optional[Operator] = None

        # Find highest precedence operator
        highest_prec = 0
        highest_prec_index: Optional[int] = None
        parenthesis_level = 0
        for i, token in enumerate(tokens):
            if token == "(":
                parenthesis_level += 1
                continue
            elif token ==  ")":
                parenthesis_level -= 1
                continue
            if parenthesis_level == 0 and token in operator_macros:
                prec = operator_macros[token]
                print(token)
                if highest_prec in [Operator.IMPLIES, Operator.EQUIVALENT] and \
                    prec in [Operator.IMPLIES, Operator.EQUIVALENT]:
                        raise AmbiguousPrecedence()
                if prec > highest_prec:
                    highest_prec = prec
                    highest_prec_index = i

        if highest_prec_index is None:
            # No operator found
            unwrapped = self._unwrap_parentheses(tokens)
            if len(unwrapped) != 1:
                # TODO: This should not be raised for '((A))` etc. which is five tokens
                # Rather this Exception should be raised if there are multiple variables but no operator
                raise Exception(f"Multiple tokens but no operator in expression: \"{' '.join(tokens)}\"")
            if not self._is_valid_var_name(unwrapped[0]):
                raise SyntaxError(f"'{tokens}' is not a valid token.")
            return Operator.NONE, None, Variable(unwrapped[0])
        else:
            # Got operator
            op = operator_macros[tokens[highest_prec_index]]
            left = tokens[:highest_prec_index]
            if left:
                left = self._unwrap_parentheses(left)
                l = Statement(" ".join(left))
            else:
                l = None

            right = tokens[highest_prec_index + 1:]
            right = self._unwrap_parentheses(right)
            r = Statement(" ".join(right))

            return op, l, r

    def _is_valid_var_name(self, name_candidate: str) -> bool:
        # TODO: Consider extending the definition of a valid variable name
        return name_candidate in ascii_uppercase

    def _unwrap_parentheses(self, it: list[str]) -> list[str]:
        if it[0] == "(" and it[-1] == ")":
            it = it[1:-1]
        return it

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

    def format(self):
        # Use cached value if available
        if self._formatted is None:
            self._formatted = self._do_format()
        return self._formatted

    def _do_format(self) -> str:
        f = self.literal
        for macro, subst in operator_macros.items():
            f = f.replace(macro, operators_as_strs[subst])
        return f

class Variable(Statement):
    """Special case for a Statement which consists of only one variable"""
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
    variables = ["A", "B", "C"]
    var_table = {var: False for var in variables}

    statements = [
            #Statement("(A or B => C) <=> (A => C) or (B => C)"),
        Statement("A <=> (A => C) and (B => C)"),
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

