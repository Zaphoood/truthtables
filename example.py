#!/usr/bin/env python3
from truthtables import Statement, Formatter, Formatting

def main():
    statements = [
        Statement("not A or B"),
        Statement("(A <=> B) and (B <=> C)"),
    ]
    f = Formatter(statements, mode=Formatting.LATEX)
    print(f.format_table())

if __name__ == "__main__":
    main()

