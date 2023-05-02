from __future__ import annotations
from enum import Enum, IntEnum, auto
from typing import Optional, Set
from string import ascii_uppercase

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
    Operator.EQUIVALENT: "⇔",
}

operators_as_latex = {
    Operator.NOT: "\\lnot",
    Operator.AND: "\\land",
    Operator.OR: "\\lor",
    Operator.IMPLIES: "\\Rightarrow",
    Operator.EQUIVALENT: "\\Leftrightarrow",
}
LATEX_TABLE_PRELUDE = "\\begin{{tabular}}{{ {columns} }}"
LATEX_TABLE_EPILOGUE = "\\end{tabular}"
LATEX_COLUMN_DELIM = " & "
LATEX_INDENT = "    "
LATEX_HLINE = LATEX_INDENT + " \\\\ \\hline"
LATEX_WRAP_CHAR = "$"
TRUE_STR = "w"
FALSE_STR = "f"

operator_macros = {
    "not": Operator.NOT,
    "and": Operator.AND,
    "or": Operator.OR,
    "eq": Operator.EQUIVALENT,
    "<=>": Operator.EQUIVALENT,
    "impl": Operator.IMPLIES,
    "=>": Operator.IMPLIES,
}


class Formatting(Enum):
    HUMAN = auto()
    LATEX = auto()


class AmbiguousPrecedenceError(Exception):
    def __init__(self, expression: Optional[str] = None):
        message = "Precedence is not defined between implication (=>) and equivalence (<=>). Please use parentheses to clarify your statement."
        if expression:
            super().__init__(message + f" In expression:\n{expression}")
        else:
            super().__init__(message)


class MalformedExpressionError(Exception):
    pass


class Statement:
    """Represent a logical statement that can be formatted nicely and whose value can be evaluated
    by providing values for its variables.

    A logical statement is represented by a binary tree with Statements as nodes, where each nodes left and right
    child are the respective sub-statements. For example, the statement "¬A ∨ B" is represented as:

           or
         /    \
      not A    B

    Note that Statements that have unary operators or no operator at all (such as "B" in the above example) have no left node.
    """

    def __init__(self, tokens: list[str] | str):
        self.literal: str
        self.operator: Operator
        self.left: Optional[Statement]
        self.right: Statement
        self.variables: Set[str]
        self._formatted: Optional[str] = None

        (
            self.literal,
            self.operator,
            self.left,
            self.right,
            self.variables,
        ) = self._parse_statement(tokens)

    def _parse_statement(
        self, tokens: list[str] | str
    ) -> tuple[str, Operator, Optional[Statement], Statement, Set[str]]:
        """Returns a callable representing the literal expression
        and an integer representing the number of arguments.

        Parantheses are allowed, other types of brackets are not.
        All tokens of the expression (including parentheses) must be separated by spaces."""
        if isinstance(tokens, str):
            tokens = tokens.strip()
            if self._is_valid_var_name(tokens):
                return tokens, Operator.NONE, None, Variable(tokens), {tokens}
            split = self._split_tokens(tokens)
            literal = tokens
        elif isinstance(tokens, list):
            split = tokens
            literal = " ".join(tokens)

        try:
            return (literal, *self._parse_substatement(split))
        except AmbiguousPrecedenceError:
            raise AmbiguousPrecedenceError(literal)

    def _split_tokens(self, literal: str) -> list[str]:
        tokens = []
        accumulator = ""
        for char in literal:
            if char in [" ", "(", ")"]:
                if accumulator:
                    tokens.append(accumulator)
                    accumulator = ""
                if char != " ":
                    tokens.append(char)
            else:
                accumulator += char
        if accumulator:
            tokens.append(accumulator)

        return tokens

    def _parse_substatement(
        self, tokens: list[str]
    ) -> tuple[Operator, Optional[Statement], Statement, Set[str]]:
        left: list[str] = []
        right: list[str] = []
        operator: Optional[Operator] = None

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
            elif token == ")":
                parenthesis_level -= 1
                continue
            if parenthesis_level == 0 and token in operator_macros:
                prec = operator_macros[token]
                if highest_prec in [Operator.IMPLIES, Operator.EQUIVALENT] and prec in [
                    Operator.IMPLIES,
                    Operator.EQUIVALENT,
                ]:
                    raise AmbiguousPrecedenceError()
                if prec > highest_prec:
                    highest_prec = prec
                    highest_prec_index = i
            if self._is_valid_var_name(token):
                n_vars += 1

        if highest_prec_index is None:
            # No operator found
            if n_vars == 0:
                raise MalformedExpressionError(
                    f"No variables and no operator in expression: \"{' '.join(tokens)}\""
                )
            elif n_vars > 1:
                raise MalformedExpressionError(
                    f"Multiple variables but no operator in expression: \"{' '.join(tokens)}\""
                )
            if not self._is_valid_var_name(tokens[0]):
                raise MalformedExpressionError(
                    f"'{tokens}' doesn't contain a valid variable name."
                )

            return Operator.NONE, None, Variable(tokens[0]), {tokens[0]}

        left = tokens[:highest_prec_index]
        right = tokens[highest_prec_index + 1 :]
        op_macro = tokens[highest_prec_index]

        if len(left) > 0:
            left_statement = Statement(self._unwrap_parentheses(left))
        else:
            left_statement = None
        right_statement = Statement(self._unwrap_parentheses(right))

        variables = (
            right_statement.variables
            if left_statement is None
            else right_statement.variables.union(left_statement.variables)
        )
        operator = operator_macros[op_macro]

        return operator, left_statement, right_statement, variables

    def _is_valid_var_name(self, name_candidate: str) -> bool:
        # TODO: Consider extending the definition of a valid variable name
        return name_candidate in ascii_uppercase

    def _unwrap_parentheses(self, literal: list[str]) -> list[str]:
        stack = []
        level = 0
        for char in literal:
            match char:
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
        if self.left is None:
            match self.operator:
                case Operator.NONE:
                    return self.right.evaluate(var_table)
                case Operator.NOT:
                    return not self.right.evaluate(var_table)
                case _:
                    raise Exception(
                        "Two operands for unary operator ({self.operator})."
                    )
        else:
            match self.operator:
                case Operator.OR:
                    return self.left.evaluate(var_table) or self.right.evaluate(
                        var_table
                    )
                case Operator.AND:
                    return self.left.evaluate(var_table) and self.right.evaluate(
                        var_table
                    )
                case Operator.IMPLIES:
                    return implication(
                        self.left.evaluate(var_table), self.right.evaluate(var_table)
                    )
                case Operator.EQUIVALENT:
                    return equivalence(
                        self.left.evaluate(var_table), self.right.evaluate(var_table)
                    )
                case _:
                    raise Exception(
                        "No left-hand operand for binary operator ({self.operator})."
                    )

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
    def __init__(self, statements: list[Statement], mode=Formatting.HUMAN) -> None:
        self.statements = statements
        self.mode = mode

        variables = set()
        for statement in self.statements:
            variables = variables.union(statement.variables)
        self.variables = list(variables)
        self.variables.sort()

    def format_table(self):
        var_table = {var: False for var in self.variables}
        self.statements = [Statement(var) for var in self.variables] + self.statements
        n_cols = len(self.statements)
        table = []
        table.append(
            [
                self.wrap_if(statement.format(mode=self.mode))
                for statement in self.statements
            ]
        )
        for i in range(2 ** len(self.variables)):
            for j, var in enumerate(reversed(self.variables)):
                var_table[var] = not ((i >> j) % 2)
            table.append(
                [
                    self.wrap_if(self.format_bool(statement(var_table)))
                    for statement in self.statements
                ]
            )

        output = ""
        match self.mode:
            case Formatting.HUMAN:
                col_delim = "   "
                before_row = ""
                after_row = ""
            case Formatting.LATEX:
                col_delim = LATEX_COLUMN_DELIM
                before_row = LATEX_INDENT
                after_row = LATEX_HLINE
                output += (
                    LATEX_TABLE_PRELUDE.format(columns="|".join("c" * n_cols)) + "\n"
                )
            case _:
                raise Exception("Exhaustive handling of Formatting in format_table()")

        output += self._table_to_str(table, col_delim, before_row, after_row)

        match self.mode:
            case Formatting.HUMAN:
                pass
            case Formatting.LATEX:
                output += "\n" + LATEX_TABLE_EPILOGUE
            case _:
                raise Exception("Exhaustive handling of Formatting in format_table()")

        return output

    def _table_to_str(
        self, table: list[list[str]], col_delim: str, before_row: str, between_rows: str
    ) -> str:
        col_widths = [
            max([len(table[row][col]) for row in range(len(table))])
            for col in range(len(table[0]))
        ]
        out = ""
        for i, row in enumerate(table):
            if before_row:
                out += before_row
            elements = []
            for j, el in enumerate(row):
                # TODO: Abstract this
                if self.mode == Formatting.HUMAN:
                    elements.append(
                        el.ljust(col_widths[j]) if self.mode == Formatting.HUMAN else el
                    )
                else:
                    elements.append(el)
            out += col_delim.join(elements)
            # Append newline if it's not the last line
            if i != len(table) - 1:
                if between_rows:
                    out += "\n" + between_rows
                out += "\n"

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
                raise Exception("Exhaustive handling of Formatting in wrap_if()")
