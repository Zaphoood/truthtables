from __future__ import annotations

from string import ascii_uppercase
from typing import Optional, Set

from truthtables.common import (
    BINARY_OPERATORS,
    OPERATOR_TO_STR,
    UNARY_OPERATORS,
    Formatting,
    Operator,
    operator_macros,
)
from truthtables.exceptions import AmbiguousPrecedenceError, MalformedExpressionError
from truthtables.util import split_tokens, unwrap_parentheses


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
            return UNARY_OPERATORS[self.operator](right)
        else:
            left = self.left.evaluate(var_table)
            right = self.right.evaluate(var_table)
            return BINARY_OPERATORS[self.operator](left, right)

    __call__ = evaluate

    def format(self, mode=Formatting.HUMAN):
        literal = self.literal
        subst_table = OPERATOR_TO_STR[mode]
        for macro, subst in operator_macros.items():
            literal = literal.replace(macro, subst_table[subst])
        return literal


class Variable(Statement):
    """Special case for a Statement which consists of only one variable"""

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, var_table: dict[str, bool]) -> bool:
        return var_table[self.name]
