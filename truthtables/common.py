from enum import Enum, IntEnum, auto
from typing import Callable


class Formatting(Enum):
    HUMAN = auto()
    LATEX = auto()


# Ordered by precedence (highest to lowest)
class Operator(IntEnum):
    NONE = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    EQUIVALENT = auto()


UNARY_OPERATORS: dict[Operator, Callable[[bool], bool]] = {
    Operator.NONE: lambda a: a,
    Operator.NOT: lambda a: not a,
}

BINARY_OPERATORS: dict[Operator, Callable[[bool, bool], bool]] = {
    Operator.AND: lambda a, b: a and b,
    Operator.OR: lambda a, b: a or b,
    Operator.IMPLIES: lambda a, b: (not a) or b,
    Operator.EQUIVALENT: lambda a, b: a == b,
}


OPERATOR_TO_STR: dict[Formatting, dict[Operator, str]] = {
    Formatting.HUMAN: {
        Operator.NOT: "¬",
        Operator.AND: "∧",
        Operator.OR: "∨",
        Operator.IMPLIES: "⇒",
        Operator.EQUIVALENT: "⇔",
    },
    Formatting.LATEX: {
        Operator.NOT: "\\lnot",
        Operator.AND: "\\land",
        Operator.OR: "\\lor",
        Operator.IMPLIES: "\\Rightarrow",
        Operator.EQUIVALENT: "\\Leftrightarrow",
    },
}
LATEX_TABLE_PROLOGUE = "\\begin{{tabular}}{{ {columns} }}"
LATEX_TABLE_EPILOGUE = "\\end{tabular}"
LATEX_COLUMN_DELIM = " & "
LATEX_INDENT = "    "
LATEX_HLINE = LATEX_INDENT + " \\\\ \\hline"
LATEX_WRAP_CHAR = "$"

BOOL_FORMAT = {
    True: "T",
    False: "F",
}

operator_macros = {
    "not": Operator.NOT,
    "and": Operator.AND,
    "or": Operator.OR,
    "eq": Operator.EQUIVALENT,
    "<=>": Operator.EQUIVALENT,
    "impl": Operator.IMPLIES,
    "=>": Operator.IMPLIES,
}
