from __future__ import annotations
from enum import Enum, IntEnum, auto
from typing import Optional, Set
from string import ascii_uppercase
from util import split_tokens, unwrap_parentheses, table_to_str

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


class MalformedExpressionError(Exception):
    pass


class AmbiguousPrecedenceError(MalformedExpressionError):
    def __init__(self, expression: Optional[str] = None):
        message = "Precedence is not defined between implication (=>) and equivalence (<=>) operators. Please use parentheses to clarify your statement."
        if expression:
            super().__init__(message + f"\nIn expression '{expression}'")
        else:
            super().__init__(message)


def is_valid_var_name(s: str) -> bool:
    # TODO: Consider extending the definition of a valid variable name
    return s in ascii_uppercase


class Statement:
    """Represent a logical statement that can be formatted nicely and whose value can be evaluated
    by providing values for its variables.

    A logical statement is represented by a binary tree with Statements as nodes, where each nodes left and right
    child are the respective sub-statements. For example, the statement "¬A ∨ B" is represented as:

           or
         /    \
      not A    B

    Note that Statements with one or no operator(s) have no left node.
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
        """Returns a callable representing the literal expression and an
        integer representing the number of arguments.

        Parantheses are allowed, other types of brackets are not. All tokens of
        the expression (including parentheses) must be separated by spaces."""
        if isinstance(tokens, str):
            tokens = tokens.strip()
            if is_valid_var_name(tokens):
                return tokens, Operator.NONE, None, Variable(tokens), {tokens}
            split = split_tokens(tokens)
            literal = tokens
        elif isinstance(tokens, list) and all(
            isinstance(token, str) for token in tokens
        ):
            split = tokens
            literal = " ".join(tokens)
        else:
            raise ValueError("'statements' must be str or list[str]")

        try:
            return (literal, *self._parse_substatement(split))
        except AmbiguousPrecedenceError:
            raise AmbiguousPrecedenceError(literal)

    def _parse_substatement(
        self, tokens: list[str]
    ) -> tuple[Operator, Optional[Statement], Statement, Set[str]]:
        left: list[str] = []
        right: list[str] = []
        operator: Optional[Operator] = None

        tokens = unwrap_parentheses(tokens)
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
            if is_valid_var_name(token):
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
            if not is_valid_var_name(tokens[0]):
                raise MalformedExpressionError(
                    f"'{tokens}' doesn't contain a valid variable name."
                )

            return Operator.NONE, None, Variable(tokens[0]), {tokens[0]}

        left = tokens[:highest_prec_index]
        right = tokens[highest_prec_index + 1 :]
        op_macro = tokens[highest_prec_index]

        if len(left) > 0:
            left_statement = Statement(unwrap_parentheses(left))
        else:
            left_statement = None
        right_statement = Statement(unwrap_parentheses(right))

        variables = (
            right_statement.variables
            if left_statement is None
            else right_statement.variables.union(left_statement.variables)
        )
        operator = operator_macros[op_macro]

        return operator, left_statement, right_statement, variables

    def evaluate(self, var_table: dict[str, bool]) -> bool:
        if self.left is None:
            right = self.right.evaluate(var_table)
            match self.operator:
                case Operator.NONE:
                    return right
                case Operator.NOT:
                    return not right
                case _:
                    raise Exception(f"Unkown unary operator ({self.operator}).")
        else:
            left = self.left.evaluate(var_table)
            right = self.right.evaluate(var_table)
            match self.operator:
                case Operator.OR:
                    return left or right
                case Operator.AND:
                    return left and right
                case Operator.IMPLIES:
                    return implies(left, right)
                case Operator.EQUIVALENT:
                    return equivalent(left, right)
                case _:
                    raise Exception(f"Unknown binary operator ({self.operator}).")

    __call__ = evaluate

    def format(self, mode=Formatting.HUMAN):
        # Use cached value if available
        if self._formatted is None:
            self._formatted = self._format(mode)
        return self._formatted

    def _format(self, mode: Formatting) -> str:
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


def implies(a: bool, b: bool) -> bool:
    if a:
        return b
    else:
        return True


def equivalent(a: bool, b: bool) -> bool:
    return a == b


class Formatter:
    def __init__(self, statements: list[Statement], mode=Formatting.HUMAN) -> None:
        self.statements = statements
        self.mode = mode
        variables = set().union(*[statement.variables for statement in statements])
        self.variables = sorted(list(variables))

    def format_table(self):
        statements = [Statement(var) for var in self.variables] + self.statements
        n_cols = len(statements)
        header = [
            self.wrap_expression(statement.format(mode=self.mode))
            for statement in statements
        ]
        table = [header]

        var_table = {var: False for var in self.variables}
        for i in range(2 ** len(self.variables)):
            for j, var in enumerate(reversed(self.variables)):
                var_table[var] = not ((i >> j) % 2)
            table.append(
                [
                    self.wrap_expression(self.format_bool(statement(var_table)))
                    for statement in statements
                ]
            )

        output = ""
        match self.mode:
            case Formatting.HUMAN:
                col_delim = "   "
                before_row = None
                between_rows = None
            case Formatting.LATEX:
                col_delim = LATEX_COLUMN_DELIM
                before_row = LATEX_INDENT
                between_rows = LATEX_HLINE

            case _:
                raise Exception("Exhaustive handling of Formatting in format_table()")

        if self.mode == Formatting.LATEX:
            output += LATEX_TABLE_PRELUDE.format(columns="|".join("c" * n_cols)) + "\n"

        output += table_to_str(
            table,
            col_delim,
            before_row,
            between_rows,
            ljust=self.mode == Formatting.HUMAN,
        )

        if self.mode == Formatting.LATEX:
            output += "\n" + LATEX_TABLE_EPILOGUE

        return output

    def format_bool(self, value: bool) -> str:
        return TRUE_STR if value else FALSE_STR

    def wrap_expression(self, a: str) -> str:
        if self.mode == Formatting.LATEX:
            return LATEX_WRAP_CHAR + a + LATEX_WRAP_CHAR
        return a
