# Truth tables

This library is used to calculate logical truth tables, with the option to format the output
into LaTeX source code.

## Installation

Simply clone the repository into your project folder.

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
formatter = Formatter([statement1, statement2], mode=Formatting.HUMAN)
```
If you want your output to be compatible with for LaTeX, use `Formatting.LATEX` instead.

Finally, print out your formatted truth table
```
print(formatter.format_table())
```

In this case, the output would be:
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
