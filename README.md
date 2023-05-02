# Truth tables

This library is used to calculate logical truth tables, with the option to format the output
into LaTeX source code.

## Requirements

- Python >= 3.10

## Usage

Import everything you need

```
from truthtables import Statement, Formatter, Formatting
```

Create logical statements

```
statement1 = Statement("not A or B")
statement2 = Statement("A => B")
```

Use can use `not`, `and`, `=>` (logical implication) and `<=>` (logical equivalence).
Variables used in the statement are extracted automatically; variable names can be any uppercase letter.

Create a Formatter using a list of statements defined earlier.

```
formatter = Formatter([statement1, statement2, ...], mode=Formatting.HUMAN)
```

If you want the output to be compatible with LaTeX, use `Formatting.LATEX` instead.

Finally, print out the formatted truth table

```
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
