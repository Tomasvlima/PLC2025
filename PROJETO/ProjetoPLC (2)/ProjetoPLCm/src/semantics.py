import sys

"""
Módulo: semantics.py
Descrição: Contém a lógica da Tabela de Símbolos (Symbol Table).

Responsabilidades:
1. Mapear nomes de variáveis (strings) para endereços de memória (offsets).
2. Gerir Escopos: Saber se estamos no programa principal (Global) ou numa função (Local).
3. Validar se variáveis e funções existem antes de serem usadas.
4. Calcular endereços de memória para a Stack Machine (Global vs Local).
"""

# ==============================================================================
# TABELA DE SÍMBOLOS
# ==============================================================================
class SymbolTable:
    def __init__(self):
        # Dicionário para variáveis globais: vivem durante todo o programa.
        # Estrutura: {'x': {'type': 'INTEGER', 'offset': 0, 'scope': 'global'}}
        self.globals = {}
        
        # Dicionário para variáveis locais: reiniciado a cada nova função.
        self.locals = {}
        
        # Dicionário para metadados de funções (tipo de retorno, argumentos).
        self.functions = {} 
        
        # Indica o escopo atual. Começa em 'global', muda para o nome da função.
        self.scope = 'global'
        
        # Contadores de endereços de memória (Offsets).
        # A VM não sabe nomes ('x'), só sabe posições (0, 1, 2).
        self.glob_offset = 0  # Próximo endereço livre na área Global
        self.loc_offset = 0   # Próximo endereço livre na Stack Frame atual
        
        # Auxiliar para calcular o endereço da variável de retorno
        self.curr_func_args = 0

    def normalize(self, n):
        """Pascal é case-insensitive (Ola == ola). Normalizamos tudo para minúsculas."""
        return n.lower()

    # --------------------------------------------------------------------------
    # GESTÃO DE VARIÁVEIS
    # --------------------------------------------------------------------------
    def add_var(self, name, type_info):
        """
        Regista uma variável na tabela correta dependendo do escopo atual.
        Atribui automaticamente o próximo offset disponível.
        """
        n = self.normalize(name)
        
        if self.scope == 'global':
            # Se estamos no main, vai para globals e usa storeg/pushg
            self.globals[n] = {
                'type': type_info, 
                'offset': self.glob_offset, 
                'scope': 'global'
            }
            self.glob_offset += 1 # Incrementa para a próxima variável não sobrepor esta
        else:
            # Se estamos numa função, vai para locals e usa storel/pushl
            self.locals[n] = {
                'type': type_info, 
                'offset': self.loc_offset, 
                'scope': 'local'
            }
            self.loc_offset += 1

    def add_arg(self, name, type_info, offset):
        """
        Regista um argumento de função.
        Nota: O offset dos argumentos é calculado no parser (geralmente negativo),
        pois eles estão na stack *antes* das variáveis locais.
        """
        n = self.normalize(name)
        self.locals[n] = {'type': type_info, 'offset': offset, 'scope': 'arg'}

    # --------------------------------------------------------------------------
    # GESTÃO DE FUNÇÕES
    # --------------------------------------------------------------------------
    def add_func(self, name, ret_type, args):
        """Guarda a assinatura da função para podermos validar chamadas depois."""
        n = self.normalize(name)
        self.functions[n] = {
            'ret': ret_type,   # Tipo de retorno (ex: INTEGER)
            'args': args,      # Lista de tipos dos argumentos
            'label': f"f{n}"   # Nome da label na VM (ex: ffactorial)
        }

    def enter_func(self, name, n_args):
        """
        Chamado quando o parser entra numa declaração de função.
        Muda o foco para o escopo local e reinicia o contador de variáveis locais.
        """
        self.scope = self.normalize(name)
        self.locals = {}      # Limpa as locais da função anterior
        self.loc_offset = 0   # Reinicia contagem de memória local
        self.curr_func_args = n_args # Necessário para calcular o offset de retorno

    def exit_func(self):
        """Chamado quando a função termina. Volta ao escopo global."""
        self.scope = 'global'
        self.locals = {} # Opcional: limpa para poupar memória, já não são acessíveis

    # --------------------------------------------------------------------------
    # LOOKUP (Procura)
    # --------------------------------------------------------------------------
    def get(self, name):
        """
        A função mais importante! Dado um nome 'x', devolve onde ele está.
        Ordem de procura:
        1. É variável Local?
        2. É o nome da própria função? (Para retorno de valor em Pascal)
        3. É variável Global?
        4. Erro.
        """
        n = self.normalize(name)
        
        # 1. Procura no Escopo Local (se não estivermos no global)
        if self.scope != 'global':
            if n in self.locals: return self.locals[n]
            
            # 2. Tratamento Especial: Retorno de Função em Pascal
            # Em Pascal, "nome_funcao := 10" define o valor de retorno.
            if n == self.scope: 
                # O valor de retorno fica na stack abaixo dos argumentos.
                # Calculamos o offset baseando-nos no número de argumentos.
                ret_off = -(self.curr_func_args + 1)
                # 'any' permite atribuir qualquer valor validado pelo parser
                return {'scope': 'return', 'offset': ret_off, 'type': 'any'}
        
        # 3. Procura no Escopo Global
        if n in self.globals: return self.globals[n]
        
        # 4. Se não encontrar em lado nenhum -> Erro Semântico (Fail-Fast)
        print(f"Erro Semântico: Variável '{name}' não definida.")
        sys.exit(1)

    def get_func(self, name):
        """Procura metadados de uma função para validar chamadas."""
        n = self.normalize(name)
        
        # Função Built-in 'length' para strings
        if n == 'length': return {'label': 'strlen', 'ret': 'INTEGER'}
        
        if n not in self.functions:
            print(f"Erro Semântico: Função '{name}' não definida.")
            sys.exit(1)
        return self.functions[n]
    

"""
    Explicação Rápida para a Defesa
Se o professor perguntar sobre este ficheiro:

-Porquê isolar?
 "Separar a Tabela de Símbolos do Parser torna o código mais limpo. 
 O Parser preocupa-se com a gramática, este ficheiro preocupa-se com endereços de memória."

-Como funciona o get?
 "Ele dá prioridade às variáveis locais. Se existir um x local e um x global, ele devolve o local (Shadowing).
 Também gere a lógica estranha do Pascal de atribuir valores ao nome da função para retornar."

-O que são os offsets? 
 "São os endereços 0, 1, 2 que usamos nas instruções pushl 0 ou storeg 1.
   Este módulo garante que nunca sobrepomos variáveis na memória."                 
"""