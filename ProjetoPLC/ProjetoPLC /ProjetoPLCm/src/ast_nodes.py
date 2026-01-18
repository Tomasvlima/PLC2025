"""
Módulo: ast_nodes.py
Descrição: Define as classes que compõem a Árvore de Sintaxe Abstrata (AST).
Cada classe representa uma construção gramatical da linguagem Pascal (ex: um If, uma Atribuição, uma Soma).

O Parser utiliza estas classes para criar objetos que representam o código lido, organizando-os
numa estrutura hierárquica (árvore) que será depois percorrida pelo Gerador de Código.
"""

class Program:
    """
    Nó Raiz da AST. Representa todo o programa Pascal.
    """
    def __init__(self, declarations, subprograms, body):
        # Lista de variáveis globais declaradas
        self.declarations = declarations
        # Lista de declarações de funções e procedimentos
        self.subprograms = subprograms
        # O bloco principal do programa (conteúdo entre BEGIN ... END.)
        self.body = body

class Block:
    """
    Representa um bloco de código sequencial (ex: dentro de um BEGIN ... END).
    """
    def __init__(self, statements):
        # Lista de instruções (statements) a serem executadas sequencialmente
        self.statements = statements

class SubProgramDecl:
    """
    Representa a declaração de uma Função ou Procedimento.
    Guarda toda a informação necessária para criar o contexto de execução na Stack.
    """
    def __init__(self, name, args, ret_type, locals_data, body, is_func):
        self.name = name            # Nome da função/procedimento
        self.args = args            # Lista de argumentos recebidos
        self.ret_type = ret_type    # Tipo de retorno (None se for Procedure)
        self.locals_data = locals_data # Dados das variáveis locais (calculados na Tabela de Símbolos)
        self.body = body            # O corpo de código da função
        self.is_func = is_func      # Booleano: True se for Function, False se for Procedure

class Assign:
    """
    Representa uma instrução de atribuição (ex: x := 10 + 2).
    """
    def __init__(self, name, expr, index_expr=None):
        self.name = name            # Nome da variável que recebe o valor
        self.expr = expr            # A expressão cujo resultado será atribuído
        self.index_expr = index_expr # Se não for None, indica que é um acesso a Array (ex: v[i] := ...)
        
        # O 'scope' é preenchido durante a análise semântica (no parser) e não na criação do nó.
        # Guardará a informação da Tabela de Símbolos (offset, tipo, se é global/local).
        self.scope = None  

class FunctionCall:
    """
    Representa a chamada de uma função ou procedimento (ex: soma(1, 2)).
    """
    def __init__(self, name, args):
        self.name = name    # Nome da função a chamar
        self.args = args    # Lista de expressões passadas como argumentos

class VarAccess:
    """
    Representa o uso de uma variável numa expressão (ex: usar 'x' numa soma).
    """
    def __init__(self, name, index_expr=None):
        self.name = name            # Nome da variável
        self.index_expr = index_expr # Se existir, estamos a ler uma posição de um Array (ex: v[0])
        self.scope = None           # Será preenchido com dados da Tabela de Símbolos (offset, tipo)

class Literal:
    """
    Representa um valor constante (número, string, booleano).
    São as 'folhas' da árvore nas expressões.
    """
    def __init__(self, value, type_name):
        self.value = value          # O valor em si (ex: 10, "ola", 1 para True)
        self.type_name = type_name  # O tipo do literal ('INTEGER', 'STRING', 'BOOLEAN')

class BinOp:
    """
    Representa qualquer operação binária (Aritmética, Lógica ou Relacional).
    Ex: A + B, A > B, A AND B.
    """
    def __init__(self, left, op, right):
        self.left = left    # O operando da esquerda (nó da AST)
        self.op = op        # O operador (ex: '+', 'DIV', 'OR')
        self.right = right  # O operando da direita (nó da AST)

class Write:
    """
    Representa as instruções de saída: write() e writeln().
    """
    def __init__(self, exprs, newline):
        self.exprs = exprs      # Lista de expressões a escrever no ecrã
        self.newline = newline  # Booleano: True se for writeln (adiciona \n no fim)

class Read:
    """
    Representa as instruções de entrada: read() e readln().
    """
    def __init__(self, name, index_expr=None):
        self.name = name            # Nome da variável onde guardar o input
        self.index_expr = index_expr # Se for array, guarda o índice onde escrever
        self.scope = None           # Dados da tabela de símbolos para saber onde guardar (storeg/storel)

# --- Estruturas de Controlo ---

class If:
    """
    Representa a estrutura condicional IF ... THEN ... ELSE.
    """
    def __init__(self, cond, then_b, else_b=None):
        self.cond = cond        # Expressão condicional (deve avaliar para Boolean)
        self.then_b = then_b    # Bloco a executar se True
        self.else_b = else_b    # Bloco a executar se False (opcional, pode ser None)

class While:
    """
    Representa o ciclo WHILE ... DO.
    """
    def __init__(self, cond, body):
        self.cond = cond    # Condição de continuação do ciclo
        self.body = body    # Corpo do ciclo

class Repeat:
    """
    Representa o ciclo REPEAT ... UNTIL.
    Nota: A condição é de paragem, avaliada no final.
    """
    def __init__(self, statements, cond):
        self.statements = statements # Lista de instruções (executa pelo menos uma vez)
        self.cond = cond             # Condição de paragem

class For:
    """
    Representa o ciclo FOR.
    Suporta tanto a direção 'TO' (incremento) como 'DOWNTO' (decremento).
    """
    def __init__(self, var, start, end, body, direction):
        self.var = var          # Nome da variável de controlo
        self.start = start      # Valor inicial
        self.end = end          # Valor final
        self.body = body        # Corpo do ciclo
        self.direction = direction # string: 'to' ou 'downto'
        self.scope = None       # Dados da variável de controlo na Tabela de Símbolos