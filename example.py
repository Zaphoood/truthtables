#!/usr/bin/env python3
from truthtables import MalformedExpressionError, Statement, Formatter, Formatting


def main():
    try:
        statements = [
            Statement("not A or B"),
            Statement("(A <=> B) and (B <=> C)"),
        ]
        f = Formatter(statements, mode=Formatting.HUMAN)
        # f = Formatter(statements, mode=Formatting.LATEX)
        print(f.format_table())
    except MalformedExpressionError as e:
        print(e)


if __name__ == "__main__":
    main()
