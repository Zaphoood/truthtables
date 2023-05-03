#!/usr/bin/env python3
from formatter import Formatter

from common import Formatting
from exceptions import MalformedExpressionError
from statement import Statement


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
