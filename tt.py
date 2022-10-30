#!/usr/bin/env python3

from __future__ import annotations
from enum import Enum, IntEnum, auto
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

operators_as_latex = {
    Operator.NOT: "\\lnot",
    Operator.AND: "\\land",
    Operator.OR: "\\lor",
    Operator.IMPLIES: "\\Rightarrow",
    Operator.EQUIVALENT: "\\Leftrightarrow"
}
LATEX_TABLE_PRELUDE = "\\begin{{tabular}}{{ {columns} }}\n    \\hline"
LATEX_TABLE_EPILOGUE = "\\end{tabular}"
LATEX_COLUMN_DELIM = " & "
LATEX_INDENT = "    "
LATEX_NEWLINE = " \\\\ \\hline"
LATEX_WRAP_CHAR = "$"
TRUE_STR = "w"
FALSE_STR = "f"

operator_macros = {
        "not":  Operator.NOT,
        "and":  Operator.AND,
        "or":   Operator.OR,
        "eq":   Operator.EQUIVALENT,
        "<=>":  Operator.EQUIVALENT,
        "impl": Operator.IMPLIES,
        "=>":   Operator.IMPLIES,
}

class Formatting(Enum):
    HUMAN = auto()
    LATEX = auto()


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

        tokens = self._unwrap_parentheses(tokens)
        # Find highest precedence operator
        highest_prec = 0
        highest_prec_index: Optional[int] = None
        parenthesis_level = 0
        n_vars = 0
        for i, token in enumerate(tokens):
            if token == "(":
                parenthesis_level += 1
                continue
            elif token ==  ")":
                parenthesis_level -= 1
                continue
            if parenthesis_level == 0 and token in operator_macros:
                prec = operator_macros[token]
                if highest_prec in [Operator.IMPLIES, Operator.EQUIVALENT] and \
                    prec in [Operator.IMPLIES, Operator.EQUIVALENT]:
                        raise AmbiguousPrecedence()
                if prec > highest_prec:
                    highest_prec = prec
                    highest_prec_index = i
            if self._is_valid_var_name(token):
                n_vars += 1

        if highest_prec_index is None:
            # No operator found
            if n_vars == 0:
                raise Exception(f"No variables and no operator in expression: \"{' '.join(tokens)}\"")
            elif n_vars > 1:
                raise Exception(f"Multiple variables but no operator in expression: \"{' '.join(tokens)}\"")
            if not self._is_valid_var_name(tokens[0]):
                raise SyntaxError(f"'{tokens}' is not a valid token.")
            return Operator.NONE, None, Variable(tokens[0])
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

    def _unwrap_parentheses(self, literal: list[str]) -> list[str]:
        stack = []
        level = 0
        for c in literal:
            match c:
                case "(":
                    stack.append(level)
                    level += 1
                case ")":
                    level -= 1
                    stack.append(level)
        while literal[0] == "(":
            if literal[-1] != ")":
                break
            if stack[0] in stack[1:-1]:
                break
            stack = stack[1:-1]
            literal = literal[1:-1]

        return literal

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

    def format(self, mode=Formatting.HUMAN):
        # Use cached value if available
        if self._formatted is None:
            self._formatted = self._do_format(mode)
        return self._formatted

    def _do_format(self, mode: Formatting) -> str:
        literal = self.literal
        match mode:
            case Formatting.HUMAN:
                subst_table = operators_as_strs
            case Formatting.LATEX:
                subst_table = operators_as_latex
            case _:
                raise Exception("Exhaustive handling of Formatting in _do_format")
        for macro, subst in operator_macros.items():
            literal = literal.replace(macro, subst_table[subst])
        return literal

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

class Formatter:
    def __init__(self, variables: list[str], statements: list[Statement], mode=Formatting.HUMAN) -> None:
        self.variables = variables
        self.statements = statements
        self.mode = mode

    def format_table(self):
        var_table = {var: False for var in self.variables}
        table = [[]]
        n_cols = len(self.variables) + len(self.statements)
        for var in self.variables:
            table[0].append(self.wrap_if(var))
        for statement in self.statements:
            table[0].append(self.wrap_if(statement.format(mode=self.mode)))

        for i in range(2 ** len(self.variables)):
            for j, var in enumerate(reversed(self.variables)):
                var_table[var] = not((i >> j) % 2)
            new_row = []
            for v in self.variables:
                new_row.append(self.wrap_if(self.format_bool(var_table[v])))
            for statement in self.statements:
                new_row.append(self.wrap_if(self.format_bool(statement(var_table))))
            table.append(new_row)

        match self.mode:
            case Formatting.HUMAN:
                col_delim = "   "
                before_row = ""
                after_row = ""
                output = ""
            case Formatting.LATEX:
                col_delim = LATEX_COLUMN_DELIM
                before_row = LATEX_INDENT
                after_row = LATEX_NEWLINE
                output = LATEX_TABLE_PRELUDE.format(columns = "|c" * n_cols + "|") + "\n"
            case _:
                raise Exception("Exhaustive handling of Fromatting in format_table()")

        output += self._table_to_str(table, col_delim, before_row, after_row)

        match self.mode:
            case Formatting.HUMAN:
                pass
            case Formatting.LATEX:
                output += "\n" + LATEX_TABLE_EPILOGUE
            case _:
                raise Exception("Exhaustive handling of Fromatting in format_table()")

        return output

    def _table_to_str(self, table: list[list[str]], col_delim: str, before_row: str, after_row: str) -> str:
        col_widths = [max([len(table[row][col]) for row in range(len(table))])
            for col in range(len(table[0]))]
        out = ""
        for i, row in enumerate(table):
            if before_row:
                out += before_row
            elements = []
            for j, el in enumerate(row):
                if self.mode == Formatting.HUMAN:
                    elements.append(el.ljust(col_widths[j]) if self.mode == Formatting.HUMAN else el)
                else:
                    elements.append(el)
            out += col_delim.join(elements)
            if after_row:
                out += after_row
            # Append newline if it's not the last line
            out += "\n" * (i != len(table) - 1)

        return out

    def format_bool(self, bool_value: bool) -> str:
        formatted = bool_value and TRUE_STR or FALSE_STR
        return formatted

    def wrap_if(self, a: str) -> str:
        def _latex_wrap(a: str) -> str:
            return LATEX_WRAP_CHAR + a + LATEX_WRAP_CHAR

        match self.mode:
            case Formatting.HUMAN:
                return a
            case Formatting.LATEX:
                return _latex_wrap(a)
            case _:
                raise Exception("Exhaustive handling of Fromatting in warp_if()")


def main():
    # TODO: Move main to separate file, untracked by git
    variables = ["A", "B", "C"]
    statements = [
        Statement("(not A and B) or (A and not B)"),
        Statement("(not A and B) or (A and not B)"),
        Statement("(A or B) and not (A and B)"),
    ]
    f = Formatter(variables, statements, mode=Formatting.LATEX)
    print(f.format_table())

if __name__ == "__main__":
    main()

