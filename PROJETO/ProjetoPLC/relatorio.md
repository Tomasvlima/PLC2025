# Relatório: Compilador de Pascal para Máquina Virtual

**Unidade Curricular:** Processamento de Linguagens e Compiladores (PLC)  
**Ano Letivo:** 2025/2026  
**Grupo:** 19  
**Autores:**
* **Rodrigo da Silva** (A108661)
* **Tomás Viana Lima** (A108488)

---

## 1. Introdução

Este projeto visa o desenvolvimento de um compilador completo para um subconjunto da linguagem **Pascal (Standard Pascal)**, capaz de traduzir código de alto nível para linguagem *Assembly* compatível com uma Máquina Virtual (VM) baseada em pilha (*Stack Machine*).

O sistema foi implementado em **Python**, utilizando a biblioteca **PLY (Python Lex-Yacc)** para a análise léxica e sintática. O objetivo central deste projeto não foi apenas a tradução de código, mas a criação de um compilador **robusto, modular e seguro**, com um foco especial na **Análise Semântica** e **Verificação de Tipos** (*Type Safety*) antes da geração de código.

---

## 2. Arquitetura do Sistema

Para garantir a escalabilidade e a manutenção do código, adotou-se uma arquitetura estritamente modular, separando a lógica de *parsing*, a gestão de memória e a definição de estruturas de dados em ficheiros distintos.

### 2.1. Organização dos Módulos

O projeto encontra-se dividido nos seguintes componentes:

1.  **`src/lexer.py` (Frontend):** Responsável pela tokenização, normalização de input (*case-insensitivity*) e filtragem de comentários.
2.  **`src/ast_nodes.py` (Estrutura de Dados):** Define as classes da Árvore de Sintaxe Abstrata (AST), permitindo uma representação hierárquica do programa em memória.
3.  **`src/semantics.py` (Motor Semântico):** Módulo dedicado exclusivamente à lógica de negócio. Contém a classe `SymbolTable`, responsável por controlar escopos (Global vs Local), calcular *offsets* de memória e gerir assinaturas de funções.
4.  **`src/parser.py` (Backend e Orquestração):** O núcleo do compilador. Contém a gramática formal (BNF), a lógica de construção da AST, o sistema de inferência de tipos e o gerador de código final.

---

## 3. Análise Léxica e Sintática

A análise sintática valida a estrutura gramatical do código fonte. A gramática foi desenhada para resolver ambiguidades comuns através da definição explícita de precedência de operadores.

* **Precedência:** Operadores multiplicativos (`*`, `/`, `DIV`, `MOD`) têm prioridade sobre aditivos (`+`, `-`), e operadores lógicos (`NOT`) têm a prioridade máxima.
* **Distinção de Operadores:** O *Lexer* distingue semanticamente a divisão real (`/`) da divisão inteira (`div`). Enquanto `/` gera sempre um resultado real, o `div` exige operandos inteiros. Esta distinção é crucial para garantir que a instrução correta é enviada para a VM.

---

## 4. Análise Semântica e Verificação de Tipos (Type Safety)

O diferencial deste compilador reside na sua capacidade de **validação semântica**. Ao contrário de tradutores simples que delegam os erros para o tempo de execução, este sistema verifica a consistência dos tipos de dados durante a compilação.

### 4.1. Tabela de Símbolos e Escopos
A classe `SymbolTable` gere o ciclo de vida das variáveis e a alocação de memória:
* **Escopo Global:** Variáveis acessíveis em todo o programa (instruções `pushg`/`storeg`).
* **Escopo Local e Argumentos:** Ao entrar numa função, cria-se um novo contexto. Os argumentos recebem *offsets* negativos (relativos ao *Frame Pointer*), enquanto as variáveis locais recebem *offsets* positivos sequenciais.

### 4.2. Lógica de Inferência de Tipos ("Guards")
Implementou-se um sistema de inferência (`infer_type`) que percorre a AST para validar operações aritméticas e de atribuição.

A função de inferência opera recursivamente (*bottom-up*). Para validar uma expressão complexa como `(A + B)`, o compilador desce até às folhas da árvore (literais e variáveis) e propaga o tipo para cima:
1.  O sistema infere o tipo de `A` e `B` consultando a Tabela de Símbolos.
2.  Se `A` for `INTEGER` e `B` for `REAL`, o sistema não só valida a operação como promove o tipo do resultado para `REAL`, garantindo coerência aritmética.
3.  Se os tipos forem incompatíveis (ex: `INTEGER` + `STRING`), a propagação é interrompida e o erro é disparado imediatamente.

### 4.3. Tratamento do tipo `ANY`
Para suportar a flexibilidade do retorno de funções em Pascal, implementou-se uma lógica especial que atribui o tipo interno `ANY` à variável de retorno da função. Isto permite a atribuição de valores sem gerar falsos positivos na verificação de tipos, mantendo a segurança nas restantes operações.

---

## 5. Geração de Código

A geração de código segue o padrão *Visitor*, percorrendo a AST validada e emitindo instruções para a Stack Machine.

### 5.1. Estruturas de Controlo
As estruturas `If`, `While` e `Repeat` são traduzidas utilizando *labels* e saltos condicionais (`JZ`, `JUMP`). O ciclo `For` é decomposto numa inicialização, verificação de limite e incremento automático, garantindo o comportamento esperado tanto em loops crescentes (`TO`) como decrescentes (`DOWNTO`).

### 5.2. Gestão de Memória (Heap e Arrays)
A implementação de Arrays utiliza alocação dinâmica na *Heap*:
1.  Na declaração, é emitida a instrução `alloc N`.
2.  No acesso (`arr[i]`), o compilador calcula o endereço da célula em tempo de execução: soma o endereço base do *pointer* ao índice desejado e utiliza `storen`/`loadn` para manipulação direta da memória.

### 5.3. Mapeamento de Instruções (AST -> VM)
A tradução das operações da árvore sintática para a *Stack Machine* é direta e eficiente. A tabela abaixo ilustra o mapeamento entre os nós da AST e as instruções de *assembly* geradas:

| Operador Pascal | Nó da AST (Python) | Instrução VM Gerada |
| :--- | :--- | :--- |
| `+` (Soma) | `BinOp(left, '+', right)` | `add` |
| `*` (Multiplicação) | `BinOp(left, '*', right)` | `mul` |
| `div` (Divisão Int) | `BinOp(left, 'DIV', right)` | `div` |
| `/` (Divisão Real) | `BinOp(left, '/', right)` | `div` |
| `and` (Lógico) | `BinOp(left, 'AND', right)` | `mul` |
| `or` (Lógico) | `BinOp(left, 'OR', right)` | `add` |
| `=` (Igualdade) | `BinOp(left, '=', right)` | `equal` |

---

## 6. Validação e Testes

O compilador foi validado através de um conjunto abrangente de testes, divididos em três categorias para garantir a conformidade funcional e a robustez.

### 6.1. Testes Base (Requisitos do Guião)
| Teste | Funcionalidade Validada | Resultado |
| :--- | :--- | :--- |
| `ola.pas` | I/O básico e Strings literais | ✅ Sucesso |
| `fatorial.pas` | Recursividade e gestão da pilha de funções | ✅ Sucesso |
| `primo.pas` | Operadores lógicos e aritmética (`mod`) | ✅ Sucesso |
| `array.pas` | Alocação dinâmica e indexação de vetores | ✅ Sucesso |
| `binario.pas` | Manipulação de Strings (`charat`) e conversão | ✅ Sucesso |

### 6.2. Testes Adicionais (Funcionalidades Extra)
| Teste | Objetivo | Resultado |
| :--- | :--- | :--- |
| `fibonacci.pas` | Lógica sequencial e atualização de variáveis | ✅ Sucesso |
| `soma.pas` | Leitura de input (`readln`) e acumulação | ✅ Sucesso |
| `temperatura.pas` | Precedência de operadores aritméticos | ✅ Sucesso |
| `div.pas` | **Distinção semântica entre divisão inteira e real** | ✅ Sucesso |

### 6.3. Testes de Robustez e Filosofia "Fail-Fast"
Estes testes foram criados para **falhar propositadamente**, provando a eficácia das guardas semânticas.

**Estratégia de Integridade (Fail-Fast):**
A arquitetura do compilador prioriza a integridade do código gerado, adotando uma estratégia de segurança estrita. Ao detetar uma incompatibilidade semântica crítica (ex: tentar somar Inteiro com String), o processo de compilação é abortado imediatamente (`sys.exit(1)`). Esta decisão de design assegura que a geração de ficheiros `.vm` só ocorre se o programa for semanticamente válido, prevenindo a criação de executáveis corrompidos ou inseguros.

| Teste | Cenário de Erro | Comportamento do Compilador |
| :--- | :--- | :--- |
| `erro_soma.pas` | Tentativa de somar Inteiro + String | 🛡️ **Bloqueado:** `Erro Semântico` detetado |
| `erro_atribuicao.pas` | Atribuir String a variável Inteira | 🛡️ **Bloqueado:** `Erro Semântico` detetado |
| `erro_div.pas` | Usar `div` com resultado Real | 🛡️ **Bloqueado:** `Erro Semântico` detetado |

---

## 7. Conclusão

O projeto resultou num compilador funcional e seguro. A arquitetura modular e a introdução da **Análise Semântica com Verificação de Tipos** elevam a qualidade da solução, garantindo que o código gerado para a VM é não só sintaticamente válido, mas também logicamente coerente. Todos os requisitos propostos foram cumpridos e superados com a implementação de validações de robustez.

---

## 8. Como Executar

**Pré-requisitos:** Python 3 e biblioteca PLY.

**Compilação:**
Para gerar o código máquina (`.vm`) a partir de um ficheiro Pascal:
```bash
./run.sh testes/nome_do_teste.pas
```