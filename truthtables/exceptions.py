from typing import Optional


class MalformedExpressionError(Exception):
    def __init__(self, message: str, expression: Optional[str] = None):
        if expression is None:
            self.message = message
        else:
            self.message = f"In expression '{expression}': " + message
        super().__init__(self.message)


class AmbiguousPrecedenceError(MalformedExpressionError):
    def __init__(self, expression: Optional[str] = None):
        message = "Precedence is not defined between implication (=>) and equivalence (<=>) operators. Please use parentheses to clarify your statement."
        super().__init__(message, expression=expression)
