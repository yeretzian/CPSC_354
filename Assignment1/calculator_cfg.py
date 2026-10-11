import sys
import math
from lark import Lark, Transformer

# make the parser from our grammar file
# (rel_to=__file__ means: look for grammar.lark in the same folder as this file)
parser = Lark.open("grammar.lark", rel_to=__file__, start="exp")


# turns the parse tree into an AST made of tuples
# each function name matches a label (-> name) in grammar.lark
class CalcTransformer(Transformer):
    def num(self, items):
        return ("num", float(items[0]))

    def plus(self, items):
        return ("plus", items[0], items[1])

    def minus(self, items):
        return ("minus", items[0], items[1])

    def times(self, items):
        return ("times", items[0], items[1])

    def pow(self, items):
        return ("pow", items[0], items[1])

    def neg(self, items):
        return ("neg", items[0])

    def log(self, items):
        return ("log", items[0], items[1])


# goes through the AST and calculates the answer (recursion!)
def evaluate(ast):
    if ast[0] == "num":
        return ast[1]
    elif ast[0] == "plus":
        return evaluate(ast[1]) + evaluate(ast[2])
    elif ast[0] == "minus":
        return evaluate(ast[1]) - evaluate(ast[2])
    elif ast[0] == "times":
        return evaluate(ast[1]) * evaluate(ast[2])
    elif ast[0] == "pow":
        return evaluate(ast[1]) ** evaluate(ast[2])
    elif ast[0] == "neg":
        return -evaluate(ast[1])
    elif ast[0] == "log":
        return math.log(evaluate(ast[1]), evaluate(ast[2]))


# main part of the program
expression = sys.argv[1]
tree = parser.parse(expression)
ast = CalcTransformer().transform(tree)
result = evaluate(ast)

# print 7 instead of 7.0 if the answer is a whole number
if result == int(result):
    print(int(result))
else:
    print(result)
