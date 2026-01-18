import sys

# ==============================================================================
# TABELA DE SÍMBOLOS
# Gere variáveis globais, locais, argumentos e funções.
# ==============================================================================
class SymbolTable:
    def __init__(self):
        self.globals = {}
        self.locals = {}
        self.functions = {} 
        self.scope = 'global'
        self.glob_offset = 0
        self.loc_offset = 0
        self.curr_func_args = 0

    def normalize(self, n): return n.lower()

    # Adiciona variável (Global ou Local dependendo do escopo atual)
    def add_var(self, name, type_info):
        n = self.normalize(name)
        if self.scope == 'global':
            self.globals[n] = {'type': type_info, 'offset': self.glob_offset, 'scope': 'global'}
            self.glob_offset += 1
        else:
            self.locals[n] = {'type': type_info, 'offset': self.loc_offset, 'scope': 'local'}
            self.loc_offset += 1

    # Adiciona argumento de função
    def add_arg(self, name, type_info, offset):
        n = self.normalize(name)
        self.locals[n] = {'type': type_info, 'offset': offset, 'scope': 'arg'}

    # Regista uma função nova
    def add_func(self, name, ret_type, args):
        n = self.normalize(name)
        self.functions[n] = {'ret': ret_type, 'args': args, 'label': f"f{n}"}

    def enter_func(self, name, n_args):
        self.scope = self.normalize(name)
        self.locals = {}
        self.loc_offset = 0
        self.curr_func_args = n_args

    def exit_func(self):
        self.scope = 'global'
        self.locals = {}

    # Procura uma variável
    def get(self, name):
        n = self.normalize(name)
        if self.scope != 'global':
            if n in self.locals: return self.locals[n]
            if n == self.scope: # Variável de retorno da função
                ret_off = -(self.curr_func_args + 1)
                return {'scope': 'return', 'offset': ret_off, 'type': 'any'}
        
        if n in self.globals: return self.globals[n]
        print(f"Erro Semântico: Variável '{name}' não definida.")
        sys.exit(1)

    # Procura uma função
    def get_func(self, name):
        n = self.normalize(name)
        if n == 'length': return {'label': 'strlen', 'ret': 'INTEGER'}
        if n not in self.functions:
            print(f"Erro Semântico: Função '{name}' não definida.")
            sys.exit(1)
        return self.functions[n]