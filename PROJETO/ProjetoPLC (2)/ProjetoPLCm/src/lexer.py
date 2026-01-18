import ply.lex as lex

"""
Módulo: lexer.py
Descrição: Responsável pela Análise Léxica (Tokenização).

O Lexer recebe o código fonte como uma string gigante e parte-o em pedaços pequenos
chamados 'Tokens' (ex: palavras reservadas, números, operadores).

Funcionalidades chave:
1. Reconhecimento de padrões usando Expressões Regulares (Regex).
2. Filtragem de comentários (não chegam ao parser).
3. Gestão de Palavras Reservadas (distinguir 'if' de uma variável chamada 'if').
4. Contagem de linhas para relatórios de erro.
"""

# ==============================================================================
# PALAVRAS RESERVADAS
# ==============================================================================
# Mapeamento de palavras-chave para o seu tipo de Token.
# Pascal é case-insensitive, por isso as chaves estão todas em minúsculas.
reserved = {
    # Estruturas de Controlo
    'program': 'PROGRAM',
    'var': 'VAR',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'for': 'FOR',
    'to': 'TO',
    'downto': 'DOWNTO',
    'repeat': 'REPEAT',
    'until': 'UNTIL',
    'function': 'FUNCTION',
    'procedure': 'PROCEDURE',
    'of': 'OF',
    'array': 'ARRAY',
    
    # Tipos de Dados
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'string': 'STRING',
    
    # I/O
    'write': 'WRITE',
    'writeln': 'WRITELN',
    'read': 'READ',
    'readln': 'READLN',
    
    # Literais Booleanos
    'true': 'TRUE',
    'false': 'FALSE',
    
    # Operadores Textuais (crucial para o Parser não confundir com variáveis)
    'div': 'DIV',   # Divisão Inteira
    'mod': 'MOD',   # Resto
    'and': 'AND',   # Lógica
    'or': 'OR',     # Lógica
    'not': 'NOT'    # Negação
}

# ==============================================================================
# LISTA DE TOKENS
# ==============================================================================
# O PLY exige esta lista 'tokens' com TODOS os nomes de tokens possíveis.
# É a soma dos tokens simples (definidos abaixo) + valores do dicionário reserved.
tokens = [
    'ID', 'NUM', 'STRING_LITERAL',
    'PLUS', 'MINUS', 'TIMES', 'SLASH', 
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'ASSIGN',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'COLON', 'SEMICOLON', 'COMMA', 'DOT', 'RANGE'
] + list(reserved.values())

# ==============================================================================
# REGRAS DE EXPRESSÕES REGULARES (REGEX)
# ==============================================================================
# Para tokens simples, basta definir uma variável t_NOMETOKEN com a Regex.

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_SLASH   = r'/'  # Divisão Real (distinta de DIV)
t_EQ      = r'='
t_NEQ     = r'<>' # Diferente em Pascal
t_LT      = r'<'
t_GT      = r'>'
t_LE      = r'<='
t_GE      = r'>='
t_ASSIGN  = r':=' # Atribuição
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COLON   = r':'
t_SEMICOLON = r';'
t_COMMA   = r','
t_DOT     = r'\.'
t_RANGE   = r'\.\.' # Para definição de Arrays (1..10)

# Caracteres a ignorar (Espaços e Tabs)
t_ignore = ' \t'

# ==============================================================================
# FUNÇÕES DE PROCESSAMENTO DE TOKENS
# ==============================================================================
# Usamos funções quando precisamos de lógica extra ao detetar o token.

def t_COMMENT(t):
    r'\{[^}]*\}'
    # Reconhece tudo entre { e }.
    # O 'pass' significa "ignora isto". Não retornamos nada, 
    # logo o Parser nunca vai saber que existiam comentários.
    pass

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Esta é a função MAIS IMPORTANTE do Lexer.
    # 1. Apanha qualquer palavra (identificador ou keyword).
    # 2. Converte para minúsculas (t.value.lower()) para case-insensitivity.
    # 3. Verifica se existe no dicionário 'reserved'.
    #    - Se existir (ex: 'if'), muda o tipo para 'IF'.
    #    - Se não existir (ex: 'soma'), mantém o tipo default 'ID'.
    t.type = reserved.get(t.value.lower(), 'ID') 
    return t

def t_NUM(t):
    r'\d+'
    # O Lexer lê tudo como texto. Aqui convertemos "123" para o inteiro 123
    # para que na AST já tenhamos números reais para fazer contas.
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'\'([^\']|\'\')*\''
    # Regex complexa para strings Pascal: 'ola''mundo' (escapar aspas simples).
    # Removemos as aspas de fora [1:-1] e tratamos o escape ('' -> ').
    t.value = t.value[1:-1].replace("''", "'") 
    return t

def t_newline(t):
    r'\n+'
    # Conta os \n para incrementar o número da linha.
    # Crucial para mensagens de erro: "Erro na linha 5".
    t.lexer.lineno += len(t.value)

def t_error(t):
    # Chamado se o Lexer encontrar um caracter que não conhece.
    print(f"Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Inicialização do Lexer
lexer = lex.lex()

"""
P: Como é que o compilador distingue o if de uma variável chamada if?
R: "Através da função t_ID. Primeiro a Regex captura a palavra. Depois,
 fazemos um lookup no dicionário reserved. Se a palavra estiver lá,
 o tipo do token muda de ID para IF. Se não estiver, assume-se que é uma variável."

P: O Pascal não distingue maiúsculas de minúsculas. Como resolveram isso?
R: "Na função t_ID, antes de verificarmos se é uma palavra reservada, 
 convertemos o input para minúsculas com t.value.lower().
 Assim, BEGIN, Begin e begin são todos identificados como o token BEGIN."

P: O que acontece aos comentários?
R: "São ignorados. A regra t_COMMENT tem apenas um pass e não retorna nada.
 O Parser (a gramática) nunca chega a receber tokens de comentário."
"""