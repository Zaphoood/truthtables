#!/usr/bin/env python3
import sys
from argparse import ArgumentParser

from truthtables import Formatter, Formatting, Statement
from truthtables.common import BOOL_FORMAT
from truthtables.exceptions import MalformedExpressionError

FORMATTING_MODES = {
    "human": Formatting.HUMAN,
    "latex": Formatting.LATEX,
}
parser = ArgumentParser(description="Truth tables calculator")
parser.add_argument("expression", nargs="+", help="An expression to evaluate")
parser.add_argument(
    "-f",
    "--format",
    nargs="?",
    action="store",
    default="human",
    choices=FORMATTING_MODES.keys(),
    help="Choose a formatting mode",
)
parser.add_argument(
    "-b",
    "--bool",
    action="store",
    help="Specify formatting for boolean values. Format is '<false>,<true>' (e.g. '0,1')",
)


def parse_bool_format(s: str, delim: str = ",") -> dict[bool, str]:
    false, true = s.split(delim, 2)[:2]
    return {True: true, False: false}


if __name__ == "__main__":
    args = parser.parse_args()
    bool_format = BOOL_FORMAT
    if args.bool is not None:
        try:
            bool_format = parse_bool_format(args.bool)
        except ValueError:
            print(f"Malformed bool format: '{args.bool}'")
            sys.exit(1)
    try:
        statements = [Statement(expression) for expression in args.expression]
    except MalformedExpressionError as e:
        print(e)
        sys.exit(1)

    table = Formatter(
        statements,
        mode=FORMATTING_MODES[args.format],
        bool_format=bool_format,
    ).format_table()
    print(table)
