# PA1 Specs: Calculator with Lark

## What the program does

This program is a calculator. It takes a math expression as a string (the concrete syntax), turns it into a tree (the abstract syntax), and then calculates the answer from the tree. You run it like this:

```
python calculator_cfg.py "1+2*3"
7
```

The program has three main steps:

1. **Parsing:** Lark uses the grammar in `grammar.lark` to turn the string into a parse tree.
2. **Making the AST:** a Transformer turns the parse tree into an abstract syntax tree (AST) made of tuples, like `('plus', ('num', 1), ('times', ('num', 2), ('num', 3)))`.
3. **Evaluating:** the `evaluate` function goes through the AST using recursion and calculates the final number.

## The grammar

### The starting grammar

The assignment started with this grammar:

```
exp -> exp '+' exp
exp -> exp '*' exp
exp -> exp '^' exp
exp -> exp '-' exp
exp -> '-' exp
exp -> 'log' exp 'base' exp
exp -> '(' exp ')'
exp -> number
```

The problem with this grammar is that it is **ambiguous**, which means some strings have more than one parse tree. For example, `1+2*3` could be parsed as `(1+2)*3 = 9` or as `1+(2*3) = 7`. The answer depends on the shape of the tree, so the calculator needs every string to have only one parse tree.

### The new grammar

To fix this, the new grammar uses the same idea from class where each **precedence level** gets its own nonterminal (`Exp`, `Exp1`, `Exp2`, and so on). `exp` is the loosest level and `exp4` is the tightest level:

```
exp  -> exp '+' exp1 | exp '-' exp1 | exp1
exp1 -> exp1 '*' exp2 | exp2
exp2 -> '-' exp2 | 'log' exp 'base' exp2 | exp3
exp3 -> exp4 '^' exp2 | exp4
exp4 -> number | '(' exp ')'
```

This grammar accepts the same strings as the starting grammar, but now each string only has one parse tree.

In `grammar.lark`, every rule also has a label like `-> plus` or `-> times`. These labels tell the Transformer which operation each part of the tree is. The `?` in front of each rule name tells Lark to skip a node if it only has one child, so the tree doesn't get filled with extra in-between nodes. `NUMBER` and `WS` (whitespace) come from Lark's built-in `common` library, and `%ignore WS` lets the user type spaces anywhere.

## Order of operations

Here are the precedence levels, from the loosest to the tightest:

| Level | Nonterminal | Operations |
|---|---|---|
| loosest | `exp` | `+` and `-` |
| | `exp1` | `*` |
| | `exp2` | negative `-` and `log ... base ...` |
| | `exp3` | `^` |
| tightest | `exp4` | numbers and `( )` |

The tighter an operation is, the further down the tree it ends up, so it gets calculated first. This order comes from the test cases:

- `1+2*3 = 7`, so `*` is tighter than `+`.
- `2^3*2 = 16` and `2^3+1 = 9`, so `^` is tighter than `*` and `+`.
- `-3^2 = -9`, so `^` is tighter than the negative sign. This means `-3^2` is `-(3^2)` and not `(-3)^2`, which matches normal math.
- `log 8 base 2 + 1 = 4`, so the `+ 1` is not part of the base. It is `(log 8 base 2) + 1`.

### Which way operations group

The grammar also decides how an operation groups when it shows up more than once in a row.

For `+`, `-`, and `*`, the rules use **left recursion** (`exp -> exp '+' exp1`), so they group from the left. For example, `1-2-3` is `(1-2)-3 = -4`. This matters for subtraction, since `1-(2-3)` would give 2 instead.

For `^`, the rule is the other way around (`exp3 -> exp4 '^' exp2`), so it groups from the right. This is why `2^3^2` is `2^(3^2) = 512` and not `(2^3)^2 = 64`. Here is the parse tree:

```
     ^
    / \
   2   ^
      / \
     3   2
```

### The negative sign and log

The negative sign and `log` are on the same level (`exp2`) because both of them come *before* the thing they apply to.

For the negative sign, `exp2 -> '-' exp2` points back to itself, so you can stack them like `--1 = 1`. Since `^` is below it, `-3^2` gets this tree:

```
    neg
     |
     ^
    / \
   3   2
```

which gives -9.

For `log X base Y`, the two parts work differently:

- `X` can be a whole `exp`, because the word `base` shows where it ends. So `log 1+3 base 2` is log of 4 base 2, which is 2.
- `Y` is only an `exp2`, so it can't grab a `+` that comes after it. This is what makes `log 8 base 2 + 1` equal 4.

The new grammar also still accepts things like `2^-1` and `2*-3`. The original grammar allows those, and since the right side of `^` and `*` can be an `exp2` (which can start with `-`), the new grammar does too.

## Methods and how they work

### The parser

```python
parser = Lark.open("grammar.lark", rel_to=__file__, start="exp")
```

This line makes the parser from the grammar file. `start="exp"` means the whole input has to be an `exp`, and `rel_to=__file__` tells Lark to find `grammar.lark` in the same folder as `calculator_cfg.py`.

### `CalcTransformer`

This class turns the parse tree from Lark into an AST made of tuples. Lark goes through the tree from the bottom up, and every time it finds a node with a label, it calls the function with that same name. `items` is a list of the node's children, which have already been turned into tuples.

- `num(items)` turns the number into a float and returns `('num', value)`.
- `plus(items)` returns `('plus', left, right)`.
- `minus(items)` returns `('minus', left, right)`.
- `times(items)` returns `('times', left, right)`.
- `pow(items)` returns `('pow', base, exponent)`.
- `neg(items)` returns `('neg', x)`.
- `log(items)` returns `('log', x, base)`.

Parentheses don't need their own function. Once the tree is built, the grouping is already shown by the shape of the tree, so the `( )` aren't needed anymore.

### `evaluate(ast)`

This function calculates the answer using **recursion**. It looks at the first part of the tuple (like `'plus'`) to see what operation it is. Then it calls itself on the smaller trees inside and combines the answers:

- `'num'` just returns the number. This is the base case, where the recursion stops.
- `'plus'`, `'minus'`, and `'times'` add, subtract, or multiply the two sides.
- `'pow'` uses Python's `**`.
- `'neg'` flips the sign.
- `'log'` uses `math.log(x, base)`.

Every call works on a smaller part of the tree, and every branch ends in a number, so the recursion always stops.

### Main part of the program

The bottom of the file reads the expression from the command line (`sys.argv[1]`), parses it, makes the AST, and evaluates it. Since the numbers are floats, the answer could come out as `7.0`. The tests want `7`, so if the answer is a whole number it gets printed as an int.

## Example: following `log 8 base 2 + 1`

1. Lark parses the string. Since `+` is on the loosest level, it ends up at the top of the tree:

    ```
          +
         / \
       log  1
       / \
      8   2
    ```

2. The Transformer turns it into `('plus', ('log', ('num', 8.0), ('num', 2.0)), ('num', 1.0))`.
3. `evaluate` calculates the log first (3.0) and then adds 1 to get 4.0.
4. The program prints `4`.

## Testing

All ten test cases from the assignment pass. Here are some extra ones to check the tricky parts:

| Input | Output | What it checks |
|---|---|---|
| `1-2-3` | -4 | subtraction groups from the left |
| `2^-1` | 0.5 | a negative after `^` still works |
| `2*-3` | -6 | a negative after `*` still works |
| `(-3)^2` | 9 | parentheses change the order |
| `log 8 base 2^3` | 1 | the base can be a power |
