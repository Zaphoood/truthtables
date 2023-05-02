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
