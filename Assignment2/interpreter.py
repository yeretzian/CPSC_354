import sys
import os
from lark import Lark, Transformer

# make the parser from our grammar file
# (rel_to=__file__ means: look for grammar.lark in the same folder as this file)
parser = Lark.open("grammar.lark", rel_to=__file__, parser="lalr")


# runs the whole program: string -> parse tree -> AST -> normal form -> string
def interpret(source_code):
    cst = parser.parse(source_code)
    ast = LambdaCalculusTransformer().transform(cst)
    result_ast = evaluate(ast)
    result = linearize(result_ast)
    return result


# turns the parse tree into an AST made of tuples
# each function name matches a label (-> name) in grammar.lark
#   ('var', name)
#   ('lam', parameter, body)
#   ('app', function, argument)
class LambdaCalculusTransformer(Transformer):
    def lam(self, args):
        name, body = args
        return ("lam", str(name), body)

    def app(self, args):
        return ("app", args[0], args[1])

    def var(self, args):
        return ("var", str(args[0]))


# reduces the AST all the way to normal form (recursion!)
# this is the part i changed. the starter version got stuck in two places:
#   1. it never went inside a lambda, so \x.((\y.y) x) stayed the same
#   2. if the function part wasn't a lambda, it never reduced the argument,
#      so a ((\x.x) b) stayed the same
# now we keep reducing in both of those places until nothing is left
def evaluate(tree):
    if tree[0] == "app":
        # first, reduce the function part
        e1 = evaluate(tree[1])
        if e1[0] == "lam":
            # it's a lambda, so do a beta step: put the argument in for the parameter
            name = e1[1]
            body = e1[2]
            argument = tree[2]
            rhs = substitute(body, name, argument)
            result = evaluate(rhs)
        else:
            # it's not a lambda (like a variable), so we can't do a beta step.
            # but the argument might still have stuff to reduce (fix #2)
            result = ("app", e1, evaluate(tree[2]))
    elif tree[0] == "lam":
        # reduce inside the body of the lambda (fix #1)
        result = ("lam", tree[1], evaluate(tree[2]))
    else:
        # a variable can't be reduced
        result = tree
    return result


# makes fresh variable names: Var1, Var2, Var3, ...
# these can never clash with names the user types, because the grammar says
# user names have to start with a lowercase letter or _ (and Var starts with V)
class NameGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self):
        self.counter += 1
        return "Var" + str(self.counter)


name_generator = NameGenerator()


# capture-avoiding substitution: tree[replacement/name]
# (replaces the free copies of name in tree with replacement)
def substitute(tree, name, replacement):
    if tree[0] == "var":
        if tree[1] == name:
            return replacement      # x[r/x] = r
        else:
            return tree             # y[r/x] = y
    elif tree[0] == "lam":
        if tree[1] == name:
            # the lambda binds name, so the copies inside are not free. leave it alone
            return tree             # (\x.e)[r/x] = \x.e
        else:
            # rename the parameter to a fresh name first, so it can't capture
            # a free variable in replacement. then substitute into the body
            # (\y.e)[r/x] = \fresh.(e[fresh/y][r/x])
            fresh_name = name_generator.generate()
            renamed_body = substitute(tree[2], tree[1], ("var", fresh_name))
            return ("lam", fresh_name, substitute(renamed_body, name, replacement))
    elif tree[0] == "app":
        return ("app", substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    else:
        raise Exception("Unknown tree", tree)


# turns the AST back into a string, with all the parentheses written out
def linearize(ast):
    if ast[0] == "var":
        return ast[1]
    elif ast[0] == "lam":
        return "(" + "\\" + ast[1] + "." + linearize(ast[2]) + ")"
    elif ast[0] == "app":
        return "(" + linearize(ast[1]) + " " + linearize(ast[2]) + ")"
    else:
        return ast


# main part of the program
# the input can be an expression or the name of a file with an expression in it
def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    input_arg = sys.argv[1]

    if os.path.isfile(input_arg):
        with open(input_arg, "r") as file:
            expression = file.read()
    else:
        expression = input_arg

    # only print the result (the tests check the output exactly)
    print(interpret(expression))


if __name__ == "__main__":
    main()


