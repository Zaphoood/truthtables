from typing import Optional


class MalformedExpressionError(Exception):
    pass


class AmbiguousPrecedenceError(MalformedExpressionError):
    def __init__(self, expression: Optional[str] = None):
        message = "Precedence is not defined between implication (=>) and equivalence (<=>) operators. Please use parentheses to clarify your statement."
        if expression:
            super().__init__(message + f"\nIn expression '{expression}'")
        else:
            super().__init__(message)
