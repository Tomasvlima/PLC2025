class Program:
    def __init__(self, declarations, subprograms, body):
        self.declarations = declarations
        self.subprograms = subprograms
        self.body = body

class Block:
    def __init__(self, statements):
        self.statements = statements

class SubProgramDecl:
    def __init__(self, name, args, ret_type, locals_data, body, is_func):
        self.name = name
        self.args = args
        self.ret_type = ret_type
        self.locals_data = locals_data
        self.body = body
        self.is_func = is_func

class Assign:
    def __init__(self, name, expr, index_expr=None):
        self.name = name
        self.expr = expr
        self.index_expr = index_expr
        self.scope = None  

class FunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class VarAccess:
    def __init__(self, name, index_expr=None):
        self.name = name
        self.index_expr = index_expr
        self.scope = None

class Literal:
    def __init__(self, value, type_name):
        self.value = value
        self.type_name = type_name

class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Write:
    def __init__(self, exprs, newline):
        self.exprs = exprs
        self.newline = newline

class Read:
    def __init__(self, name, index_expr=None):
        self.name = name
        self.index_expr = index_expr
        self.scope = None

# --- Estruturas de Controlo ---

class If:
    def __init__(self, cond, then_b, else_b=None):
        self.cond = cond
        self.then_b = then_b
        self.else_b = else_b

class While:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class Repeat:
    def __init__(self, statements, cond):
        self.statements = statements
        self.cond = cond

class For:
    def __init__(self, var, start, end, body, direction):
        self.var = var
        self.start = start
        self.end = end
        self.body = body
        self.direction = direction
        self.scope = None