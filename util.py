def split_tokens(literal: str) -> list[str]:
    tokens = []
    accumulator = ""
    for char in literal:
        if char in [" ", "(", ")"]:
            if accumulator:
                tokens.append(accumulator)
                accumulator = ""
            if char != " ":
                tokens.append(char)
        else:
            accumulator += char
    if accumulator:
        tokens.append(accumulator)

    return tokens


def unwrap_parentheses(literal: list[str]) -> list[str]:
    stack = []
    level = 0
    for char in literal:
        match char:
            case "(":
                stack.append(level)
                level += 1
            case ")":
                level -= 1
                stack.append(level)
    while literal[0] == "(":
        if literal[-1] != ")":
            break
        if stack[0] in stack[1:-1]:
            break
        stack = stack[1:-1]
        literal = literal[1:-1]

    return literal


def table_to_str(
    table: list[list[str]],
    col_delim: str,
    before_row: str,
    between_rows: str,
    ljust: bool = False,
) -> str:
    col_widths = [
        max([len(table[row][col]) for row in range(len(table))])
        for col in range(len(table[0]))
    ]
    out = ""
    for i, row in enumerate(table):
        if before_row:
            out += before_row
        elements = [
            el.ljust(col_widths[j]) if ljust else el for j, el in enumerate(row)
        ]
        out += col_delim.join(elements)
        # TODO: Use "\n".join for this
        # Append newline if it's not the last line
        if i != len(table) - 1:
            if between_rows:
                out += "\n" + between_rows
            out += "\n"

    return out
