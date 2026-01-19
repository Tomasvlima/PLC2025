import ply.yacc as yacc
from lexer import tokens  # Importamos os tokens definidos no Lexer
from ast_nodes import * # Importamos as classes da AST para criar a estrutura em memória
from semantics import SymbolTable # Importamos a Tabela de Símbolos (Memória e Escopos)
import sys # Necessário para sys.exit(1) quando detetamos erros
import os  # Necessário para manipular nomes de ficheiros

"""
Módulo: parser.py
Descrição: O Coração do Compilador.

Este ficheiro tem 4 grandes responsabilidades:
1. Definir a Gramática (Regras BNF) que o PLY usa para entender o código.
2. Construir a AST (Árvore de Sintaxe Abstrata) à medida que lê o código.
3. Validar a Semântica (Verificar tipos incompatíveis) -> AS TUAS "GUARDAS".
4. Gerar o Código Assembly final para a Máquina Virtual.
"""

# ==============================================================================
# VARIÁVEIS GLOBAIS E FUNÇÕES AUXILIARES
# ==============================================================================

# A Tabela de Símbolos global. 
# É instanciada aqui para ser acessível por todas as regras gramaticais.
# Ela guarda quem são as variáveis, os seus tipos e os seus endereços (offsets).
st = SymbolTable()

# Lista que vai acumular as instruções Assembly (ex: ["pushi 0", "storeg 0", ...]).
# No final, esta lista é escrita no ficheiro .vm.
instrs = []

# Contador para gerar labels únicos (L1, L2, L3...) para os saltos condicionais (If/While).
label_count = 0

def new_label():
    """Gera uma nova etiqueta única (ex: 'L5') para usar nos JUMP/JZ."""
    global label_count
    label_count += 1
    return f"L{label_count}"

def emit(s):
    """Adiciona uma instrução textual à lista final de instruções."""
    instrs.append(s)

# ==============================================================================
# INFERÊNCIA DE TIPOS (Type Checking) - O CÉREBRO SEMÂNTICO
# ==============================================================================
def infer_type(node):
    """
    Função Recursiva (Bottom-Up) que descobre o tipo de qualquer nó da AST.
    
    COMO FUNCIONA:
    Ela desce até às folhas da árvore (números ou variáveis) e sobe com a resposta.
    É fundamental para as tuas 'Guardas Semânticas'.
    """
    
    # Caso Base 1: Se o nó é um Literal (ex: 10, 'ola'), o tipo já está no objeto.
    if isinstance(node, Literal):
        return node.type_name

    # Caso Base 2: Se o nó é uma Variável, temos de ir à Tabela de Símbolos perguntar.
    elif isinstance(node, VarAccess):
        if not node.scope: return 'UNKNOWN' # Proteção contra erros internos
        t = node.scope.get('type')
        
        # CASO ESPECIAL: Acesso a Array (ex: vetor[1])
        # Se a variável é um Array, mas tem index_expr, então estamos a aceder a um elemento.
        # Logo, o tipo não é 'ARRAY', mas sim o tipo base (ex: INTEGER).
        if node.index_expr:
            if isinstance(t, dict) and t.get('kind') == 'array':
                return str(t['base']).upper()
        
        # Se for o array inteiro sem índice
        if isinstance(t, dict): return 'ARRAY'
        return str(t).upper()

    # Caso Recursivo: Operações Binárias (A + B)
    elif isinstance(node, BinOp):
        op = node.op.upper()
        
        # Operadores Relacionais (>, <, =, <>) resultam SEMPRE em BOOLEAN.
        if op in ['=', '<>', '<', '>', '<=', '>=']: return 'BOOLEAN'
        
        # A Divisão Real (/) resulta SEMPRE em REAL, mesmo que dividas inteiros (5 / 2 = 2.5).
        if op == '/': return 'REAL' 
        
        # Para +, -, *, DIV: Assumimos que o tipo resultante é igual ao tipo do operando da esquerda.
        # Nota: A verificação se eles são compatíveis acontece noutro lado (no 'gen'). 
        # Aqui só queremos saber "se tudo correr bem, que tipo isto devolve?".
        return infer_type(node.left)

    # Chamadas de Função (ex: soma(1,2))
    elif isinstance(node, FunctionCall):
        # A função 'length' é interna do Pascal e devolve sempre Inteiro.
        if node.name.lower() == 'length': return 'INTEGER' 
        try:
            # Vamos à tabela ver qual o tipo de retorno declarado para a função.
            info = st.get_func(node.name)
            if info and info['ret']: return str(info['ret']).upper()
        except: pass
        return 'UNKNOWN'

    # Se não conseguirmos descobrir, devolvemos UNKNOWN (para evitar crashes).
    return 'UNKNOWN'

# ==============================================================================
# GERADOR DE CÓDIGO (Assembly da VM) - Padrão Visitor
# ==============================================================================
def gen(node):
    """
    Esta função percorre a AST completa e gera as instruções para a Máquina Virtual.
    É aqui que aplicas a filosofia 'Fail-Fast': validação antes da geração.
    """
    
    # --- 1. PROGRAMA PRINCIPAL ---
    if isinstance(node, Program):
        emit("start") # Instrução obrigatória de início da VM
        
        # ALOCAÇÃO GLOBAL:
        # Percorremos todas as variáveis globais da Tabela de Símbolos.
        # Ordenamos pelo 'offset' para garantir que alocamos na ordem certa (0, 1, 2...).
        for v in sorted(st.globals.values(), key=lambda x: x['offset']):
            kind = v['type']
            
            # Se for Array, usamos 'alloc N' (Alocação dinâmica na Heap)
            if isinstance(kind, dict) and kind['kind']=='array':
                emit(f"alloc {kind['size']}")
            # Se for String, inicializamos com "0" (String vazia/default)
            elif str(kind).upper() == 'STRING':
                emit('pushs "0"') 
            # Inteiros e Booleanos começam a 0
            else:
                emit("pushi 0")
        
        # SALTO PARA O MAIN:
        # As funções estão declaradas antes do corpo principal.
        # Temos de saltar por cima delas para não as executar sem serem chamadas.
        l_main = new_label()
        emit(f"jump {l_main}")
        
        # Gera código para as funções (que ficam "arrumadas" no topo do executável)
        for sub in node.subprograms: gen(sub)
        
        # Aqui começa a execução real do programa
        emit(f"{l_main}:")
        gen(node.body)
        emit("stop") # Fim do programa

    # --- 2. DECLARAÇÃO DE FUNÇÕES/PROCEDIMENTOS ---
    elif isinstance(node, SubProgramDecl):
        # Cria a label da função (ex: 'ffatorial:') para onde o CALL vai saltar
        emit(f"f{st.normalize(node.name)}:") 
        
        # ALOCAÇÃO LOCAL:
        # Variáveis locais precisam de espaço na Stack Frame.
        # Filtramos apenas as locais (offset >= 0). Argumentos (offset < 0) já lá estão.
        locs = [v for v in node.locals_data if v['offset'] >= 0]
        
        # Descobre qual o maior offset para saber quantas posições reservar
        max_off = -1
        for v in locs: 
            if v['offset'] > max_off: max_off = v['offset']
        
        # Cria um mapa para saber o que alocar em cada posição
        alloc_map = {}
        for v in locs:
            kind = v['type']
            if isinstance(kind, dict): alloc_map[v['offset']] = f"alloc {kind['size']}"
            elif str(kind).upper() == 'STRING': alloc_map[v['offset']] = 'pushs "0"'
        
        # Emite os allocs/pushi sequencialmente
        for i in range(max_off + 1):
            if i in alloc_map: emit(alloc_map[i])
            else: emit("pushi 0")
        
        gen(node.body) # Gera o código do corpo da função
        emit("return") # Retorna o controlo a quem chamou

    # --- 3. BLOCO DE CÓDIGO (BEGIN ... END) ---
    elif isinstance(node, Block):
        # Simplesmente gera código para cada instrução, uma a seguir à outra.
        for s in node.statements: gen(s)

    # --- 4. ATRIBUIÇÃO (Variável := Expressão) ---
    elif isinstance(node, Assign):
        info = node.scope # Obtém dados da variável da Tabela de Símbolos
        
        # ====================================================
        # [GUARDA SEMÂNTICA] VERIFICAÇÃO DE TIPOS (Type Safety)
        # ====================================================
        var_type = str(info['type']).upper()
        # Se for array, queremos saber o tipo base dos elementos
        if isinstance(info['type'], dict): 
             var_type = str(info['type']['base']).upper() if node.index_expr else 'ARRAY'
        
        # 1. Descobrir o tipo da expressão que estamos a tentar atribuir
        expr_type = infer_type(node.expr)
        
        # 2. Validar compatibilidade
        if expr_type != 'UNKNOWN' and var_type != 'UNKNOWN' and var_type != 'ANY':
             # Exceção: Permitir atribuir Inteiro a Real (o sistema promove)
             if var_type == 'REAL' and expr_type == 'INTEGER': pass
             # Se forem diferentes -> ERRO! O Fail-Fast aborta aqui.
             elif var_type != expr_type:
                 print(f"⚠️  ERRO SEMÂNTICO: Tentativa de atribuir {expr_type} a uma variável {var_type} ('{node.name}')")
                 sys.exit(1)
        # ====================================================

        # LÓGICA ESPECIAL: Retorno de Função (nome_funcao := valor)
        if info['scope'] == 'return':
            gen(node.expr)
            emit(f"storel {info['offset']}") # Guarda no local especial de retorno
            return

        off = info['offset']
        # Decide se usa instrução Global (storeg) ou Local (storel)
        base = "storeg" if info['scope'] == 'global' else "storel"
        
        if node.index_expr:
            # ATRIBUIÇÃO A ARRAY (v[i] := x)
            # 1. Coloca o endereço base do array (Pointer) na stack
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            # 2. Calcula o índice 'i'
            gen(node.index_expr) 
            # 3. Ajuste de índice (Pascal 1..N vs VM 0..N-1) -> Subtrai 1
            emit("pushi 1")
            emit("sub")
            # 4. Gera o valor 'x'
            gen(node.expr)
            # 5. Guarda na Heap ('storen': guarda valor no endereço Pointer+Index)
            emit("storen") 
        else:
            # ATRIBUIÇÃO SIMPLES
            gen(node.expr)
            emit(f"{base} {off}")

    # --- 5. CHAMADA DE FUNÇÃO (Call) ---
    elif isinstance(node, FunctionCall):
        # 'length' é tratado como instrução nativa da VM
        if node.name.lower() == 'length':
            gen(node.args[0])
            emit("strlen")
            return
        
        info = st.get_func(node.name)
        
        # Se a função tem retorno (não é Procedure), reservamos espaço na stack (pushi 0)
        # Esse espaço será preenchido pela função chamada antes de retornar.
        if info['ret']: emit("pushi 0")
        
        # Colocamos os argumentos na stack
        for arg in node.args: gen(arg)
        
        # Chamamos a função (Salta para a Label dela)
        emit(f"pusha {info['label']}")
        emit("call")
        
        # Limpeza da Stack: Removemos os argumentos usados, pois já não são precisos.
        if node.args: emit(f"pop {len(node.args)}")

    # --- 6. ACESSO A VARIÁVEIS (Ler valor) ---
    elif isinstance(node, VarAccess):
        info = node.scope
        off = info['offset']
        base = "pushg" if info['scope'] == 'global' else "pushl"
        
        if node.index_expr:
            # LEITURA DE ARRAY (valor := v[i])
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            gen(node.index_expr)
            emit("pushi 1")
            emit("sub")
            
            t = info.get('type')
            if str(t).upper() == 'STRING': 
                emit("charat") # Instrução especial para ler caracter de String
            else: 
                emit("loadn")  # Instrução normal para ler da Heap
        else:
            # LEITURA SIMPLES
            emit(f"{base} {off}")

    # --- 7. OPERAÇÕES BINÁRIAS (+, -, *, DIV...) ---
    elif isinstance(node, BinOp):
        # ====================================================
        # [GUARDA SEMÂNTICA] VALIDAÇÃO DE OPERAÇÕES
        # ====================================================
        t_left = infer_type(node.left)
        t_right = infer_type(node.right)
        op = node.op.upper()

        # Guarda 1: DIV e MOD exigem INTEIROS. Não funcionam com Reais.
        if op in ['DIV', 'MOD']:
            if (t_left != 'INTEGER' and t_left != 'UNKNOWN') or \
               (t_right != 'INTEGER' and t_right != 'UNKNOWN'):
                print(f"⚠️  ERRO SEMÂNTICO: Operador '{op}' exige Inteiros. Recebeu {t_left} e {t_right}.")
                sys.exit(1)
        
        # Guarda 2: Aritmética só funciona com Números (Int ou Real). Strings dão erro.
        if op in ['+', '-', '*']:
            if t_left != t_right and 'UNKNOWN' not in (t_left, t_right):
                 if not ({t_left, t_right} <= {'INTEGER', 'REAL'}):
                     print(f"⚠️  ERRO SEMÂNTICO: Operação '{op}' inválida entre {t_left} e {t_right}.")
                     sys.exit(1)
        # ====================================================

        # Gera código para os operandos (esquerda e direita)
        gen(node.left)
        gen(node.right)
        
        # Mapa de tradução: Operador Pascal -> Instrução VM
        ops = {'+':'add','-':'sub','*':'mul','/':'div','DIV':'div','MOD':'mod',
               'AND':'mul','OR':'add','=':'equal','<>':'equal\nnot',
               '<':'inf','>':'sup','<=':'infeq','>=':'supeq'}
        
        # Tratamento especial para Diferente (<>): Igualdade + Negação
        if op == '<>': 
            emit("equal")
            emit("not")
        else: 
            emit(ops.get(op, 'add'))

    # --- 8. LITERAIS (Constantes) ---
    elif isinstance(node, Literal):
        if node.type_name == 'STRING': emit(f'pushs "{node.value}"')
        else: emit(f"pushi {node.value}")

    # --- 9. ESCRITA (WRITE/WRITELN) ---
    elif isinstance(node, Write):
        for e in node.exprs:
            gen(e) # Gera o valor a escrever
            
            # Decide qual instrução usar (writes para texto, writei para números)
            if isinstance(e, Literal) and e.type_name == 'STRING':
                emit("writes")
            elif isinstance(e, VarAccess):
                t = e.scope.get('type')
                if str(t).upper() == 'STRING': emit("writes")
                else: emit("writei")
            else:
                emit("writei") # Default
                
        if node.newline: # Se for Writeln, adiciona quebra de linha
            emit('pushs "\\n"')
            emit("writes")

    # --- 10. LEITURA (READ/READLN) ---
    elif isinstance(node, Read):
        info = node.scope
        off = info['offset']
        base = "storeg" if info['scope'] == 'global' else "storel"
        
        if node.index_expr:
            # Ler para Array: precisa de Pointer, Index, Valor
            if info['scope'] == 'global': emit(f"pushg {off}")
            else: emit(f"pushl {off}")
            gen(node.index_expr)
            emit("pushi 1")
            emit("sub")
            emit("read") # Lê string do teclado
            emit("atoi") # Converte para Inteiro
            emit("storen") # Guarda na Heap
        else:
            # Ler para Variável Simples
            emit("read")
            t = info.get('type')
            if str(t).upper() != 'STRING': emit("atoi") # Converte se não for String
            emit(f"{base} {off}")

    # --- 11. ESTRUTURAS DE CONTROLO ---
    
    # IF ... THEN ... ELSE
    elif isinstance(node, If):
        l1, l2 = new_label(), new_label()
        gen(node.cond)     # Gera a condição (True/1 ou False/0)
        emit(f"jz {l1}")   # Jump Zero: Se for 0 (falso), salta para o Else (L1)
        gen(node.then_b)   # Executa o bloco THEN
        if node.else_b:
            emit(f"jump {l2}") # Se executou o THEN, salta o ELSE (vai para L2)
            emit(f"{l1}:")     # Label do ELSE
            gen(node.else_b)   # Executa o bloco ELSE
            emit(f"{l2}:")     # Label de FIM
        else:
            emit(f"{l1}:")     # Se não houver ELSE, L1 é o fim.

    # WHILE ... DO
    elif isinstance(node, While):
        l1, l2 = new_label(), new_label()
        emit(f"{l1}:")     # Label de INÍCIO (para o loop voltar aqui)
        gen(node.cond)     # Avalia condição
        emit(f"jz {l2}")   # Se falso, salta para o FIM (L2)
        gen(node.body)     # Executa corpo
        emit(f"jump {l1}") # Volta incondicionalmente ao início
        emit(f"{l2}:")     # Label de FIM
        
    # REPEAT ... UNTIL
    elif isinstance(node, Repeat):
        l1 = new_label()
        emit(f"{l1}:")     # Label de INÍCIO
        for s in node.statements: 
            gen(s)         # Executa corpo (pelo menos uma vez)
        gen(node.cond)     # Avalia condição DE PARAGEM
        emit(f"jz {l1}")   # Se falso (ainda não parou), volta ao início

    # FOR ... DO
    elif isinstance(node, For):
        info = node.scope
        # Prepara instruções de acesso à variável de controlo
        push = f"pushg {info['offset']}" if info['scope']=='global' else f"pushl {info['offset']}"
        store = f"storeg {info['offset']}" if info['scope']=='global' else f"storel {info['offset']}"
        
        # 1. Inicialização (i := start)
        gen(node.start)
        emit(store)
        
        l1, l2 = new_label(), new_label()
        emit(f"{l1}:") # Início do Loop
        
        # 2. Teste de Limite
        emit(push)
        gen(node.end)
        if node.direction == 'to': emit("infeq") # i <= end
        else: emit("supeq")                      # i >= end (downto)
        emit(f"jz {l2}") # Se limite passou, sai
        
        # 3. Corpo
        gen(node.body)
        
        # 4. Incremento/Decremento Automático
        emit(push)
        emit("pushi 1")
        if node.direction == 'to': emit("add")
        else: emit("sub")
        emit(store)
        
        emit(f"jump {l1}") # Volta ao início
        emit(f"{l2}:")

# ==============================================================================
# REGRAS DO PARSER (Gramática BNF)
# ==============================================================================

# Define a PRECEDÊNCIA dos operadores.
# Resolve ambiguidades como "2 + 3 * 4". Sem isto, o parser não sabe se faz (2+3)*4 ou 2+(3*4).
# A lista está ordenada do MENOS prioritário para o MAIS prioritário.
precedence = (
    ('left', 'OR'), ('left', 'AND'),                        # Lógicos (Baixa prioridade)
    ('nonassoc', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'),      # Relacionais
    ('left', 'PLUS', 'MINUS'),                              # Aditivos
    ('left', 'TIMES', 'DIV', 'MOD', 'SLASH'),               # Multiplicativos
    ('right', 'NOT'),                                       # Unário (Alta prioridade)
    ('nonassoc', 'THEN'), ('nonassoc', 'ELSE'),             # Evitar conflito do "Dangling Else"
)

# --- PROGRAMA ---
def p_program(p):
    """ program : header declarations subprograms declarations BEGIN block END DOT """
    # Regra Raiz. Constrói o nó principal da AST.
    p[0] = Program(p[2], p[3], Block(p[6]))
    
    # Inicia o processo de Geração de Código
    global instrs
    instrs = []
    gen(p[0]) # Chama o Visitante
    
    # Escreve o resultado no ficheiro .vm
    base = os.path.splitext(filename)[0]
    with open(f"{base}.vm", 'w') as f:
        f.write("\n".join(instrs) + "\n")
    print(f"[-] Compilação Sucesso: {base}.vm")

def p_header(p): 
    """ header : PROGRAM ID SEMICOLON """
    pass

# --- DECLARAÇÕES ---
def p_declarations(p): 
    """ declarations : VAR var_list 
                     | """
    pass # As variáveis são processadas dentro de var_line

def p_var_list(p): 
    """ var_list : var_line 
                 | var_list var_line """
    pass

def p_var_line(p):
    """ var_line : id_list COLON type_def SEMICOLON """
    # Momento crucial: Ao ler a declaração, adicionamos logo à Tabela de Símbolos.
    for name in p[1]: st.add_var(name, p[3])

def p_id_list(p):
    """ id_list : ID 
                | id_list COMMA ID """
    # Permite declarar várias variáveis na mesma linha: "var a, b, c : integer;"
    p[0] = [p[1]] if len(p)==2 else p[1] + [p[3]]

# --- DEFINIÇÃO DE TIPOS ---
def p_type_def(p):
    """ type_def : INTEGER 
                 | BOOLEAN 
                 | STRING 
                 | ARRAY LBRACKET NUM RANGE NUM RBRACKET OF type_def """
    if len(p) == 2: p[0] = p[1] # Tipos simples
    else: 
        # Arrays: Guardamos metadados (limite inferior, tamanho total, tipo base)
        # Tamanho = (Fim - Inicio) + 1
        p[0] = {'kind': 'array', 'lower': int(p[3]), 'size': int(p[5])-int(p[3])+1, 'base': p[8]}

# --- SUBPROGRAMAS (Funções/Procedimentos) ---
def p_subprograms(p):
    """ subprograms : subprograms subprogram 
                    | """
    p[0] = [] if len(p)==1 else p[1] + [p[2]]

def p_subprogram(p):
    """ subprogram : func_head vars_local compound_stmt SEMICOLON 
                   | proc_head vars_local compound_stmt SEMICOLON """
    head = p[1]
    # Filtramos as variáveis locais deste escopo para guardar na AST
    locals_data = [v for v in st.locals.values() if v['offset'] >= 0]
    p[0] = SubProgramDecl(head['name'], head['args'], head['ret'], locals_data, p[3], head['is_func'])
    
    # Ao terminar a leitura da função, saímos do escopo (voltamos ao Global)
    st.exit_func()

def p_func_head(p):
    """ func_head : FUNCTION ID args_decl COLON type_def SEMICOLON """
    # 1. Regista função na tabela global
    st.add_func(p[2], p[5], p[3])
    # 2. Entra no escopo local (reinicia offsets locais)
    st.enter_func(p[2], len(p[3]))
    # 3. Regista os argumentos (com offsets negativos na stack)
    for i, (n, t) in enumerate(p[3]):
        st.add_arg(n, t, i - len(p[3]))
    p[0] = {'name': p[2], 'args': p[3], 'ret': p[5], 'is_func': True}

# --- PROCEDIMENTOS (Funções sem retorno) ---
def p_proc_head(p):
    """ proc_head : PROCEDURE ID args_decl SEMICOLON """
    # 1. Regista o procedimento na Tabela de Símbolos.
    #    Nota: 'ret' é None porque procedimentos não retornam valor.
    st.add_func(p[2], None, p[3])
    
    # 2. Entra no escopo local (prepara offsets para variáveis locais).
    st.enter_func(p[2], len(p[3]))
    
    # 3. Regista os argumentos.
    #    Os argumentos têm offsets negativos na stack (ex: -1, -2...)
    #    porque são empurrados antes da função começar.
    for i, (n, t) in enumerate(p[3]):
        st.add_arg(n, t, i - len(p[3]))
        
    # Retorna um dicionário com metadados para o nó SubProgramDecl
    p[0] = {'name': p[2], 'args': p[3], 'ret': None, 'is_func': False}

# --- PROCESSAMENTO DE ARGUMENTOS ---
def p_args_decl(p):
    """ args_decl : LPAREN arg_list RPAREN 
                  | """
    # Se houver parênteses, devolve a lista de argumentos.
    # Se estiver vazio (regra vazia), devolve lista vazia [].
    p[0] = [] if len(p)==1 else p[2]

def p_arg_list(p):
    """ arg_list : arg_item 
                 | arg_list SEMICOLON arg_item """
    # Constrói a lista de argumentos recursivamente.
    # Se tivermos (a:int; b:int), junta as listas.
    p[0] = p[1] if len(p)==2 else p[1] + [p[3]]

def p_arg_item(p):
    """ arg_item : id_list COLON type_def """
    # Processa grupos de argumentos do mesmo tipo (ex: "a, b : integer").
    # Cria uma lista de tuplos: [('a', 'INTEGER'), ('b', 'INTEGER')]
    p[0] = [(n, p[3]) for n in p[1]]

def p_vars_local(p): 
    """ vars_local : declarations """
    pass # As variáveis já foram registadas na ST dentro de 'declarations'

# --- BLOCOS E STATEMENTS ---
def p_block(p): 
    """ block : statements """
    p[0] = p[1] # Passa a lista de statements para cima

def p_statements(p):
    """ statements : statement 
                   | statements SEMICOLON statement """
    # Regra Recursiva à Esquerda:
    # 1. Se for apenas um statement (len=2), cria uma lista nova: [stmt]
    # 2. Se for "statements ; statement", pega na lista acumulada (p[1]) 
    #    e adiciona o novo elemento: p[1] + [p[3]]
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
    # O "hub" central. Qualquer comando Pascal cai aqui.
    # Se a regra for vazia (ex: ; extra), cria um Bloco vazio para não dar erro.
    p[0] = p[1] if len(p)>1 else Block([]) 

def p_repeat_stmt(p):
    """ repeat_stmt : REPEAT statements UNTIL expression """
    # Cria o nó Repeat. Diferente do While, a condição é verificada no fim.
    p[0] = Repeat(p[2], p[4])

def p_func_call_stmt(p):
    """ func_call_stmt : ID LPAREN expr_list RPAREN """
    # Chamada de função como instrução independente (ex: myFunc(10);)
    p[0] = FunctionCall(p[1], p[3])

def p_compound_stmt(p):
    """ compound_stmt : BEGIN statements END """
    # Agrupa várias instruções num único Bloco (Block).
    # Essencial para IFs e Loops com várias linhas.
    p[0] = Block(p[2])

# --- ATRIBUIÇÃO ---
def p_assignment(p):
    """ assignment : ID ASSIGN expression
                   | ID LBRACKET expression RBRACKET ASSIGN expression """
    # 1. Verifica imediatamente se a variável existe na Tabela de Símbolos.
    info = st.get(p[1]) 
    
    if len(p) == 4: 
        # Atribuição Simples: x := 10
        p[0] = Assign(p[1], p[3])
        p[0].scope = info # Guarda info para o gerador saber onde gravar (offset)
    else: 
        # Atribuição a Array: v[i] := 10
        p[0] = Assign(p[1], p[6], index_expr=p[3])
        p[0].scope = info

# --- EXPRESSÕES (Matemática e Lógica) ---
def p_expression_binop(p):
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
    # Cria nó binário. A precedência (ordem das operações) é gerida
    # automaticamente pela tupla 'precedence' definida no topo do ficheiro.
    p[0] = BinOp(p[1], p[2], p[3])

def p_expression_atoms(p):
    """ expression : NUM 
                   | STRING_LITERAL 
                   | TRUE 
                   | FALSE 
                   | LPAREN expression RPAREN """
    if len(p) == 4: 
        p[0] = p[2] # Remove parênteses: (A) -> A
    elif p.slice[1].type == 'NUM':
        p[0] = Literal(p[1], 'INTEGER')
    elif p.slice[1].type == 'STRING_LITERAL':
        # TRUQUE IMPORTANTE:
        # Em Pascal, 'a' pode ser um Char ou uma String.
        # Se tiver tamanho 1, tratamos como Inteiro (ASCII) para permitir
        # comparações e manipulações matemáticas simples.
        if len(p[1]) == 1:
            p[0] = Literal(ord(p[1]), 'INTEGER')
        else:
            p[0] = Literal(p[1], 'STRING')
    elif p.slice[1].type == 'TRUE':
        p[0] = Literal(1, 'BOOLEAN') # True vira 1 na VM
    elif p.slice[1].type == 'FALSE':
        p[0] = Literal(0, 'BOOLEAN') # False vira 0 na VM

def p_expression_call_or_var(p):
    """ expression : ID 
                   | ID LPAREN expr_list RPAREN 
                   | ID LBRACKET expression RBRACKET """
    if len(p) == 2:
        # Ambiguidade: 'x' pode ser variável ou chamada de função sem argumentos.
        # Tentamos buscar como variável na Tabela de Símbolos. 
        # Se falhar (não é var), assumimos que é uma função.
        info = st.get(p[1])
        try:
            p[0] = VarAccess(p[1]); p[0].scope = info
        except:
            p[0] = FunctionCall(p[1], [])
    elif p[2] == '(': 
        # Chamada de função explícita: soma(a,b)
        p[0] = FunctionCall(p[1], p[3])
    else: 
        # Acesso a Array: v[i]
        info = st.get(p[1])
        p[0] = VarAccess(p[1], index_expr=p[3]); p[0].scope = info

# --- INPUT / OUTPUT ---
def p_io(p):
    """ write_stmt : WRITELN LPAREN expr_list RPAREN 
                   | WRITE LPAREN expr_list RPAREN """
    # Deteta se é WRITELN (com \n) ou WRITE normal
    p[0] = Write(p[3], (p[1].upper() == 'WRITELN'))

def p_read(p):
    """ read_stmt : READLN LPAREN ID RPAREN 
                  | READLN LPAREN ID LBRACKET expression RBRACKET RPAREN """
    # Verifica onde vamos guardar o valor lido
    info = st.get(p[3])
    if len(p)==5: 
        p[0] = Read(p[3]); p[0].scope = info
    else: 
        # Leitura para posição de array: readln(v[i])
        p[0] = Read(p[3], index_expr=p[5]); p[0].scope = info

# --- ESTRUTURAS DE CONTROLO ---
def p_control(p):
    """ if_stmt : IF expression THEN statement 
                | IF expression THEN statement ELSE statement """
    # Suporta IF com e sem ELSE.
    p[0] = If(p[2], p[4]) if len(p)==5 else If(p[2], p[4], p[6])

def p_while(p):
    """ while_stmt : WHILE expression DO statement """
    p[0] = While(p[2], p[4])

def p_for(p):
    """ for_stmt : FOR ID ASSIGN expression TO expression DO statement 
                 | FOR ID ASSIGN expression DOWNTO expression DO statement """
    # Suporta TO (incremento) e DOWNTO (decremento).
    # Guarda a direção (.lower()) para o gerador saber qual usar.
    p[0] = For(p[2], p[4], p[6], p[8], p[5].lower()); p[0].scope = st.get(p[2])

def p_expr_list(p):
    """ expr_list : expression
                  | expr_list COMMA expression """
    # Cria lista de expressões (ex: args de função ou itens do writeln)
    p[0] = [p[1]] if len(p)==2 else p[1] + [p[3]]

# --- TRATAMENTO DE ERROS SINTÁTICOS ---
def p_error(p):
    if p: print(f"Erro Sintaxe: '{p.value}' linha {p.lineno}")
    else: print("Erro: Fim inesperado")
    sys.exit(1)

# Inicializa o parser com as regras definidas acima
parser = yacc.yacc()

# ==============================================================================
# BLOCO PRINCIPAL (ENTRY POINT)
# ==============================================================================
if __name__ == '__main__':
    # Verifica argumentos da linha de comando
    if len(sys.argv) < 2: print("Uso: python3 src/parser.py <ficheiro.pas>")
    else:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f: 
                # Lê o ficheiro e remove carriage returns do Windows
                content = f.read().replace('\r', '') 
                # Inicia a compilação
                parser.parse(content)
        except FileNotFoundError: print("Ficheiro não encontrado")