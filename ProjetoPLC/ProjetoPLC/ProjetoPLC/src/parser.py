import ply.yacc as yacc
from lexer import tokens
from ast_nodes import *
from semantics import SymbolTable
import sys
import os

# ==============================================================================
# VARIÁVEIS GLOBAIS E FUNÇÕES AUXILIARES
# ==============================================================================

st = SymbolTable()
instrs = []
label_count = 0

def new_label():
    global label_count
    label_count += 1
    return f"L{label_count}"

def emit(s):
    instrs.append(s)

# ==============================================================================
# INFERÊNCIA DE TIPOS (Type Checking)
# ==============================================================================
def infer_type(node):
    if isinstance(node, Literal):
        return node.type_name

    elif isinstance(node, VarAccess):
        if not node.scope: return 'UNKNOWN'
        t = node.scope.get('type')
        if node.index_expr:
            if isinstance(t, dict) and t.get('kind') == 'array':
                return str(t['base']).upper()
        if isinstance(t, dict): return 'ARRAY'
        return str(t).upper()

    elif isinstance(node, BinOp):
        op = node.op.upper()
        if op in ['=', '<>', '<', '>', '<=', '>=']: return 'BOOLEAN'
        if op == '/': return 'REAL' # Divisão real devolve sempre REAL
        return infer_type(node.left)

    elif isinstance(node, FunctionCall):
        if node.name.lower() == 'length': return 'INTEGER'
        try:
            info = st.get_func(node.name)
            if info and info['ret']: return str(info['ret']).upper()
        except: pass
        return 'UNKNOWN'

    return 'UNKNOWN'

# ==============================================================================
# GERADOR DE CÓDIGO (Assembly da VM)
# ==============================================================================
def gen(node):
    if isinstance(node, Program):
        emit("start")
        for v in sorted(st.globals.values(), key=lambda x: x['offset']):
            kind = v['type']
            if isinstance(kind, dict) and kind['kind']=='array':
                emit(f"alloc {kind['size']}")
            elif str(kind).upper() == 'STRING':
                emit('pushs "0"') 
            else:
                emit("pushi 0")
        
        l_main = new_label()
        emit(f"jump {l_main}")
        for sub in node.subprograms: gen(sub)
        emit(f"{l_main}:")
        gen(node.body)
        emit("stop")

    elif isinstance(node, SubProgramDecl):
        emit(f"f{st.normalize(node.name)}:")
        locs = [v for v in node.locals_data if v['offset'] >= 0]
        max_off = -1
        for v in locs: 
            if v['offset'] > max_off: max_off = v['offset']
        
        alloc_map = {}
        for v in locs:
            kind = v['type']
            if isinstance(kind, dict): alloc_map[v['offset']] = f"alloc {kind['size']}"
            elif str(kind).upper() == 'STRING': alloc_map[v['offset']] = 'pushs "0"'
        
        for i in range(max_off + 1):
            if i in alloc_map: emit(alloc_map[i])
            else: emit("pushi 0")
        
        gen(node.body)
        emit("return")

    elif isinstance(node, Block):
        for s in node.statements: gen(s)

    elif isinstance(node, Assign):
        info = node.scope
        # --- VERIFICAÇÃO DE TIPOS ---
        var_type = str(info['type']).upper()
        if isinstance(info['type'], dict): 
             var_type = str(info['type']['base']).upper() if node.index_expr else 'ARRAY'
        
        expr_type = infer_type(node.expr)
        
        if expr_type != 'UNKNOWN' and var_type != 'UNKNOWN' and var_type != 'ANY':
             if var_type == 'REAL' and expr_type == 'INTEGER': pass
             elif var_type != expr_type:
                 print(f"⚠️  ERRO SEMÂNTICO: Tentativa de atribuir {expr_type} a uma variável {var_type} ('{node.name}')")
                 sys.exit(1)
        # ----------------------------

        if info['scope'] == 'return':
            gen(node.expr)
            emit(f"storel {info['offset']}")
            return

        off = info['offset']
        base = "storeg" if info['scope'] == 'global' else "storel"
        
        if node.index_expr:
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            gen(node.index_expr)
            emit("pushi 1")
            emit("sub")
            gen(node.expr)
            emit("storen")
        else:
            gen(node.expr)
            emit(f"{base} {off}")

    elif isinstance(node, FunctionCall):
        if node.name.lower() == 'length':
            gen(node.args[0])
            emit("strlen")
            return
        
        info = st.get_func(node.name)
        if info['ret']: emit("pushi 0")
        for arg in node.args: gen(arg)
        emit(f"pusha {info['label']}")
        emit("call")
        if node.args: emit(f"pop {len(node.args)}")

    elif isinstance(node, VarAccess):
        info = node.scope
        off = info['offset']
        base = "pushg" if info['scope'] == 'global' else "pushl"
        
        if node.index_expr:
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            gen(node.index_expr)
            emit("pushi 1")
            emit("sub")
            t = info.get('type')
            if str(t).upper() == 'STRING': 
                emit("charat")
            else: 
                emit("loadn")
        else:
            emit(f"{base} {off}")

    elif isinstance(node, BinOp):
        # --- VERIFICAÇÃO DE TIPOS ---
        t_left = infer_type(node.left)
        t_right = infer_type(node.right)
        op = node.op.upper()

        if op in ['DIV', 'MOD']:
            if (t_left != 'INTEGER' and t_left != 'UNKNOWN') or \
               (t_right != 'INTEGER' and t_right != 'UNKNOWN'):
                print(f"⚠️  ERRO SEMÂNTICO: Operador '{op}' exige Inteiros. Recebeu {t_left} e {t_right}.")
                sys.exit(1)
        
        if op in ['+', '-', '*']:
            if t_left != t_right and 'UNKNOWN' not in (t_left, t_right):
                 if not ({t_left, t_right} <= {'INTEGER', 'REAL'}):
                     print(f"⚠️  ERRO SEMÂNTICO: Operação '{op}' inválida entre {t_left} e {t_right}.")
                     sys.exit(1)
        # ----------------------------

        gen(node.left)
        gen(node.right)
        ops = {'+':'add','-':'sub','*':'mul','/':'div','DIV':'div','MOD':'mod',
               'AND':'mul','OR':'add','=':'equal','<>':'equal\nnot',
               '<':'inf','>':'sup','<=':'infeq','>=':'supeq'}
        
        if op == '<>': 
            emit("equal")
            emit("not")
        else: 
            emit(ops.get(op, 'add'))

    elif isinstance(node, Literal):
        if node.type_name == 'STRING': emit(f'pushs "{node.value}"')
        else: emit(f"pushi {node.value}")

    elif isinstance(node, Write):
        for e in node.exprs:
            gen(e)
            if isinstance(e, Literal) and e.type_name == 'STRING':
                emit("writes")
            elif isinstance(e, VarAccess):
                t = e.scope.get('type')
                if str(t).upper() == 'STRING': emit("writes")
                else: emit("writei")
            else:
                emit("writei")
        if node.newline:
            emit('pushs "\\n"')
            emit("writes")

    elif isinstance(node, Read):
        info = node.scope
        off = info['offset']
        base = "storeg" if info['scope'] == 'global' else "storel"
        if node.index_expr:
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            gen(node.index_expr)
            emit("pushi 1")
            emit("sub")
            emit("read")
            emit("atoi")
            emit("storen")
        else:
            emit("read")
            t = info.get('type')
            if str(t).upper() != 'STRING': emit("atoi")
            emit(f"{base} {off}")

    elif isinstance(node, If):
        l1, l2 = new_label(), new_label()
        gen(node.cond)
        emit(f"jz {l1}")
        gen(node.then_b)
        if node.else_b:
            emit(f"jump {l2}")
            emit(f"{l1}:")
            gen(node.else_b)
            emit(f"{l2}:")
        else:
            emit(f"{l1}:")

    elif isinstance(node, While):
        l1, l2 = new_label(), new_label()
        emit(f"{l1}:")
        gen(node.cond)
        emit(f"jz {l2}")
        gen(node.body)
        emit(f"jump {l1}")
        emit(f"{l2}:")
        
    elif isinstance(node, Repeat):
        l1 = new_label()
        emit(f"{l1}:")
        for s in node.statements: 
            gen(s)
        gen(node.cond)
        emit(f"jz {l1}")

    elif isinstance(node, For):
        info = node.scope
        push = f"pushg {info['offset']}" if info['scope']=='global' else f"pushl {info['offset']}"
        store = f"storeg {info['offset']}" if info['scope']=='global' else f"storel {info['offset']}"
        gen(node.start)
        emit(store)
        l1, l2 = new_label(), new_label()
        emit(f"{l1}:")
        emit(push)
        gen(node.end)
        if node.direction == 'to': emit("infeq")
        else: emit("supeq")
        emit(f"jz {l2}")
        gen(node.body)
        emit(push)
        emit("pushi 1")
        if node.direction == 'to': emit("add")
        else: emit("sub")
        emit(store)
        emit(f"jump {l1}")
        emit(f"{l2}:")

# ==============================================================================
# REGRAS DO PARSER (Gramática BNF)
# ==============================================================================

precedence = (
    ('left', 'OR'), ('left', 'AND'),
    ('nonassoc', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'), ('left', 'TIMES', 'DIV', 'MOD', 'SLASH'), 
    ('right', 'NOT'), ('nonassoc', 'THEN'), ('nonassoc', 'ELSE'), 
)

def p_program(p):
    """ program : header declarations subprograms declarations BEGIN block END DOT """
    p[0] = Program(p[2], p[3], Block(p[6]))
    global instrs
    instrs = []
    gen(p[0])
    
    base = os.path.splitext(filename)[0]
    with open(f"{base}.vm", 'w') as f:
        f.write("\n".join(instrs) + "\n")
    print(f"[-] Compilação Sucesso: {base}.vm")

def p_header(p): 
    """ header : PROGRAM ID SEMICOLON """
    pass

def p_declarations(p): 
    """ declarations : VAR var_list 
                     | """
    pass

def p_var_list(p): 
    """ var_list : var_line 
                 | var_list var_line """
    pass

def p_var_line(p):
    """ var_line : id_list COLON type_def SEMICOLON """
    for name in p[1]: st.add_var(name, p[3])

def p_id_list(p):
    """ id_list : ID 
                | id_list COMMA ID """
    p[0] = [p[1]] if len(p)==2 else p[1] + [p[3]]

def p_type_def(p):
    """ type_def : INTEGER 
                 | BOOLEAN 
                 | STRING 
                 | ARRAY LBRACKET NUM RANGE NUM RBRACKET OF type_def """
    if len(p) == 2: p[0] = p[1]
    else: p[0] = {'kind': 'array', 'lower': int(p[3]), 'size': int(p[5])-int(p[3])+1, 'base': p[8]}

def p_subprograms(p):
    """ subprograms : subprograms subprogram 
                    | """
    p[0] = [] if len(p)==1 else p[1] + [p[2]]

def p_subprogram(p):
    """ subprogram : func_head vars_local compound_stmt SEMICOLON 
                   | proc_head vars_local compound_stmt SEMICOLON """
    head = p[1]
    locals_data = [v for v in st.locals.values() if v['offset'] >= 0]
    p[0] = SubProgramDecl(head['name'], head['args'], head['ret'], locals_data, p[3], head['is_func'])
    st.exit_func()

def p_func_head(p):
    """ func_head : FUNCTION ID args_decl COLON type_def SEMICOLON """
    st.add_func(p[2], p[5], p[3])
    st.enter_func(p[2], len(p[3]))
    for i, (n, t) in enumerate(p[3]):
        st.add_arg(n, t, i - len(p[3]))
    p[0] = {'name': p[2], 'args': p[3], 'ret': p[5], 'is_func': True}

def p_proc_head(p):
    """ proc_head : PROCEDURE ID args_decl SEMICOLON """
    st.add_func(p[2], None, p[3])
    st.enter_func(p[2], len(p[3]))
    for i, (n, t) in enumerate(p[3]):
        st.add_arg(n, t, i - len(p[3]))
    p[0] = {'name': p[2], 'args': p[3], 'ret': None, 'is_func': False}

def p_args_decl(p):
    """ args_decl : LPAREN arg_list RPAREN 
                  | """
    p[0] = [] if len(p)==1 else p[2]

def p_arg_list(p):
    """ arg_list : arg_item 
                 | arg_list SEMICOLON arg_item """
    p[0] = p[1] if len(p)==2 else p[1] + [p[3]]

def p_arg_item(p):
    """ arg_item : id_list COLON type_def """
    p[0] = [(n, p[3]) for n in p[1]]

def p_vars_local(p): 
    """ vars_local : declarations """
    pass

def p_block(p): 
    """ block : statements """
    p[0] = p[1]

def p_statements(p):
    """ statements : statement 
                   | statements SEMICOLON statement """
    p[0] = [p[1]] if len(p)==2 else p[1] + [p[3]]

def p_statement(p):
    """ statement : assignment 
                  | write_stmt 
                  | read_stmt 
                  | if_stmt 
                  | while_stmt 
                  | repeat_stmt
                  | for_stmt 
                  | func_call_stmt 
                  | compound_stmt 
                  | """
    p[0] = p[1] if len(p)>1 else Block([]) 

def p_repeat_stmt(p):
    """ repeat_stmt : REPEAT statements UNTIL expression """
    p[0] = Repeat(p[2], p[4])

def p_func_call_stmt(p):
    """ func_call_stmt : ID LPAREN expr_list RPAREN """
    p[0] = FunctionCall(p[1], p[3])

def p_compound_stmt(p):
    """ compound_stmt : BEGIN statements END """
    p[0] = Block(p[2])

def p_assignment(p):
    """ assignment : ID ASSIGN expression
                   | ID LBRACKET expression RBRACKET ASSIGN expression """
    info = st.get(p[1])
    if len(p) == 4: p[0] = Assign(p[1], p[3]); p[0].scope = info
    else: p[0] = Assign(p[1], p[6], index_expr=p[3]); p[0].scope = info

def p_expression_binop(p):
    # Correção: Adicionada a regra 'expression SLASH expression'
    """ expression : expression PLUS expression
                   | expression MINUS expression
                   | expression TIMES expression
                   | expression DIV expression 
                   | expression SLASH expression
                   | expression MOD expression
                   | expression EQ expression
                   | expression NEQ expression
                   | expression LT expression
                   | expression LE expression
                   | expression GT expression
                   | expression GE expression 
                   | expression AND expression
                   | expression OR expression """
    p[0] = BinOp(p[1], p[2], p[3])

def p_expression_atoms(p):
    """ expression : NUM 
                   | STRING_LITERAL 
                   | TRUE 
                   | FALSE 
                   | LPAREN expression RPAREN """
    if len(p) == 4: 
        p[0] = p[2]
    elif p.slice[1].type == 'NUM':
        p[0] = Literal(p[1], 'INTEGER')
    elif p.slice[1].type == 'STRING_LITERAL':
        if len(p[1]) == 1:
            p[0] = Literal(ord(p[1]), 'INTEGER')
        else:
            p[0] = Literal(p[1], 'STRING')
    elif p.slice[1].type == 'TRUE':
        p[0] = Literal(1, 'BOOLEAN')
    elif p.slice[1].type == 'FALSE':
        p[0] = Literal(0, 'BOOLEAN')

def p_expression_call_or_var(p):
    """ expression : ID 
                   | ID LPAREN expr_list RPAREN 
                   | ID LBRACKET expression RBRACKET """
    if len(p) == 2:
        info = st.get(p[1])
        try:
            p[0] = VarAccess(p[1]); p[0].scope = info
        except:
            p[0] = FunctionCall(p[1], [])
    elif p[2] == '(': 
        p[0] = FunctionCall(p[1], p[3])
    else: 
        info = st.get(p[1])
        p[0] = VarAccess(p[1], index_expr=p[3]); p[0].scope = info

def p_io(p):
    """ write_stmt : WRITELN LPAREN expr_list RPAREN 
                   | WRITE LPAREN expr_list RPAREN """
    p[0] = Write(p[3], (p[1].upper() == 'WRITELN'))

def p_read(p):
    """ read_stmt : READLN LPAREN ID RPAREN 
                  | READLN LPAREN ID LBRACKET expression RBRACKET RPAREN """
    info = st.get(p[3])
    if len(p)==5: p[0] = Read(p[3]); p[0].scope = info
    else: p[0] = Read(p[3], index_expr=p[5]); p[0].scope = info

def p_control(p):
    """ if_stmt : IF expression THEN statement 
                | IF expression THEN statement ELSE statement """
    p[0] = If(p[2], p[4]) if len(p)==5 else If(p[2], p[4], p[6])

def p_while(p):
    """ while_stmt : WHILE expression DO statement """
    p[0] = While(p[2], p[4])

def p_for(p):
    """ for_stmt : FOR ID ASSIGN expression TO expression DO statement 
                 | FOR ID ASSIGN expression DOWNTO expression DO statement """
    p[0] = For(p[2], p[4], p[6], p[8], p[5].lower()); p[0].scope = st.get(p[2])

def p_expr_list(p):
    """ expr_list : expression
                  | expr_list COMMA expression """
    p[0] = [p[1]] if len(p)==2 else p[1] + [p[3]]

def p_error(p):
    if p: print(f"Erro Sintaxe: '{p.value}' linha {p.lineno}")
    else: print("Erro: Fim inesperado")
    sys.exit(1)

parser = yacc.yacc()

if __name__ == '__main__':
    if len(sys.argv) < 2: print("Uso: python3 src/parser.py <ficheiro.pas>")
    else:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f: 
                content = f.read().replace('\r', '') 
                parser.parse(content)
        except FileNotFoundError: print("Ficheiro não encontrado")