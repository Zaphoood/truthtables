from .common import (
    LATEX_COLUMN_DELIM,
    LATEX_HLINE,
    LATEX_INDENT,
    LATEX_TABLE_PROLOGUE,
    LATEX_TABLE_EPILOGUE,
    LATEX_WRAP_CHAR,
    BOOL_FORMAT,
    Formatting,
)
from .statement import Statement
from .util import table_to_str


class Formatter:
    def __init__(
        self,
        statements: list[Statement],
        mode: Formatting = Formatting.HUMAN,
        bool_format: dict[bool, str] = BOOL_FORMAT,
        reverse: bool = False,
    ) -> None:
        self.statements = statements
        self.mode = mode
        variables = set().union(*[statement.variables for statement in statements])
        self.variables = sorted(list(variables))
        self.bool_format = bool_format
        self.reverse = reverse

    def format_table(self):
        statements = [Statement(var) for var in self.variables] + self.statements
        n_cols = len(statements)
        header = [
            self.wrap_expression(statement.format(mode=self.mode))
            for statement in statements
        ]
        table = [header]

        var_table = {var: False for var in self.variables}
        values = range(2 ** len(self.variables))
        if self.reverse:
            values = reversed(values)
        for i in values:
            for j, var in enumerate(reversed(self.variables)):
                var_table[var] = bool((i >> j) % 2)
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
            output += LATEX_TABLE_PROLOGUE.format(columns="|".join("c" * n_cols)) + "\n"

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
        return self.bool_format[value]

    def wrap_expression(self, a: str) -> str:
        if self.mode == Formatting.LATEX:
            return LATEX_WRAP_CHAR + a + LATEX_WRAP_CHAR
        return a
