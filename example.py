#!/usr/bin/env python3
from truthtables import Formatter, Formatting, Statement
from truthtables.exceptions import MalformedExpressionError


def main():
    try:
        statements = [
            Statement("A and B and (A or not C)"),
        ]
        f = Formatter(statements, mode=Formatting.HUMAN)
        print(f.format_table())
    except MalformedExpressionError as e:
        print(e)


if __name__ == "__main__":
    main()
