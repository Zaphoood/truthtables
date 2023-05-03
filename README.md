# Truth tables 🧮

A library for generating [truth tables](https://en.wikipedia.org/wiki/Truth_table) with support for LaTeX source code output.

## Requirements

- Python >= 3.10

## Usage

Import everything you need

```python
from truthtables import Statement, Formatter, Formatting
```

Create logical statements

```python
statement1 = Statement("not A or B")
statement2 = Statement("A => B")
```

You can use `not`, `and`, `=>` (logical implication) and `<=>` (logical equivalence).
Variables used in the statement are extracted automatically; variable names can be any uppercase letter.

Create a Formatter using a list of statements defined earlier.

```python
formatter = Formatter([statement1, statement2, ...], mode=Formatting.HUMAN)
```

If you want the output to be compatible with LaTeX, use `Formatting.LATEX` instead.

Finally, print out the formatted truth table

```python
print(formatter.format_table())
```

For the above example the output would be:

```
A   B   ¬ A ∨ B   A ⇒ B
w   w   w         w
w   f   f         f
f   w   w         w
f   f   w         w
```

Please note that you cannot concatenate multiple operators of the same precedence,
e. g. `A <=> B <=> C`. To work around this, use parentheses and/or restructure the statement
(in this case, you could use `(A <=> B) and (B <=> C)`)

### Handling exceptions

```python
from truthtables.exceptions import MalformedExpressionError

try:
  s = Statement("A not B")
except MalformedExpressionError as e:
    print(e)
```

## Command Line Interface

```
Usage: cli.py [-h] [-f [{human,latex}]] [-b BOOL] expression [expression ...]

positional arguments:
  expression            An expression to evaluate

options:
  -h, --help            show this help message and exit
  -f [{human,latex}], --format [{human,latex}]
                        Choose a formatting mode
  -b BOOL, --bool BOOL  Specify formatting for boolean values. Format is
                        '<false>,<true>' (e.g. '0,1')
```
