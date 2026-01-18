import ply.lex as lex

# Palavras Reservadas do Pascal
reserved = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'string': 'STRING',
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
    'write': 'WRITE',
    'writeln': 'WRITELN',
    'read': 'READ',
    'readln': 'READLN',
    'true': 'TRUE',
    'false': 'FALSE',
    # --- OPERADORES TEXTUAIS ---
    'div': 'DIV',
    'mod': 'MOD',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT'
}

# Lista de Tokens
tokens = [
    'ID', 'NUM', 'STRING_LITERAL',
    'PLUS', 'MINUS', 'TIMES', 'SLASH', 
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'ASSIGN',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'COLON', 'SEMICOLON', 'COMMA', 'DOT', 'RANGE'
] + list(reserved.values())

# Expressões Regulares (Regex) para operadores
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_SLASH   = r'/'  
t_EQ      = r'='
t_NEQ     = r'<>'
t_LT      = r'<'
t_GT      = r'>'
t_LE      = r'<='
t_GE      = r'>='
t_ASSIGN  = r':='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COLON   = r':'
t_SEMICOLON = r';'
t_COMMA   = r','
t_DOT     = r'\.'
t_RANGE   = r'\.\.'

# Ignorar espaços e tabs
t_ignore = ' \t'

# Ignorar Comentários Pascal { ... }
def t_COMMENT(t):
    r'\{[^}]*\}'
    pass

# Reconhecimento de Identificadores e Palavras Reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID') # Verifica se é reservada (incluindo div, mod, and...)
    return t

# Reconhecimento de Números
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Reconhecimento de Strings
def t_STRING_LITERAL(t):
    r'\'([^\']|\'\')*\''
    t.value = t.value[1:-1].replace("''", "'") 
    return t

# Contagem de Linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Tratamento de Erros Léxicos
def t_error(t):
    print(f"Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Construir o Lexer
lexer = lex.lex()