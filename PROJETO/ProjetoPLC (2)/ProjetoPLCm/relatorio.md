# Guião de Defesa: Compilador Pascal (Grupo 19)

## 1. Introdução e Objetivos

O nosso projeto consistiu no desenvolvimento de um compilador para a linguagem **Pascal Standard**, capaz de traduzir o código de alto nível para linguagem *assembly* compatível com a máquina virtual.

Desde o início, o nosso objetivo principal foi a **Engenharia de Software** e a **Robustez**. O foco foi criar um compilador seguro, capaz de impedir erros lógicos e de tipos antes mesmo de gerar o código final, garantindo a fiabilidade da execução.

Utilizámos **Python** e a biblioteca **PLY**, tirando partido da sua flexibilidade para criar uma arquitetura modular.

---

## 2. Arquitetura Modular

Para garantir um código limpo e fácil de manter, estruturámos o sistema em quatro componentes essenciais:

* **`lexer.py`:** Responsável pela análise léxica, identificação de tokens e filtragem de comentários.
* **`ast_nodes.py`:** Define a estrutura da nossa **AST** (Árvore de Sintaxe Abstrata), onde cada nó representa uma construção lógica da linguagem.
* **`semantics.py`:** Este módulo centraliza a lógica de gestão de memória e escopos. Aqui reside a nossa Tabela de Símbolos, que calcula os endereços (*offsets*) para variáveis globais e locais.
* **`parser.py`:** O orquestrador central, que combina a gramática com a validação semântica para gerar o código final.

---

## 3. Análise Léxica e Sintática

Nesta fase, o objetivo foi validar a estrutura gramatical e resolver ambiguidades típicas de compiladores. Desenhámos a gramática com regras de precedência explícitas:

* **Precedência:** Definimos que operadores multiplicativos (`*`, `/`, `DIV`, `MOD`) têm prioridade sobre os aditivos, e os lógicos (`NOT`) têm a prioridade máxima.
* **Distinção de Operadores:** O *Lexer* distingue semanticamente a divisão real (`/`) da divisão inteira (`div`). Enquanto `/` gera sempre resultados reais, o `div` exige inteiros. Esta diferenciação antecipada é crucial para gerar a instrução correta para a VM mais à frente.
---

## 4. Análise Semântica e "Type Safety"

A componente de **Análise Semântica** integra um sistema de **Inferência de Tipos e Guardas** que atua diretamente sobre a AST.

A nossa abordagem funciona da seguinte forma:

1.  Antes de gerar código para uma operação, o compilador "interroga" a árvore para validar os tipos dos operandos.
2.  Utilizamos uma função recursiva `infer_type` que valida a compatibilidade entre dados.
3.  Se detetarmos uma operação ilegal — como somar um Inteiro com uma String — ativamos o protocolo **Fail-Fast**.

**Fail-Fast:** O compilador aborta imediatamente o processo (`sys.exit`). Esta decisão garante a integridade do sistema: só geramos o ficheiro `.vm` se tivermos a certeza absoluta de que o código é seguro e semanticamente correto.

---

## 5. Gestão de Memória e Geração de Código

Na tradução para a Máquina Virtual, gerimos a memória de forma híbrida:

* **Stack (Pilha):** Utilizamos a pilha para variáveis escalares e argumentos. O nosso motor semântico calcula automaticamente os *offsets* (positivos para locais, negativos para argumentos) para garantir o acesso correto.
* **Heap (Monte):** Para estruturas complexas como **Arrays**, utilizamos a alocação dinâmica (`alloc`). O acesso aos dados é feito calculando o endereço em tempo de execução, o que permite arrays flexíveis.

Também resolvemos o desafio do retorno de funções em Pascal implementando um tipo interno `ANY`, permitindo que a variável de retorno receba valores sem quebrar a verificação de tipos rigorosa.

---

## 6. Validação e Testes

Validámos o compilador com dois conjuntos de testes distintos:

1.  **Testes Funcionais:** Implementámos os testes exigidos no enunciado, mas também criámos outros para validar funcionalidades extra. Todos geram o output esperado na VM.
2.  **Testes de Robustez:** Criámos casos de erro intencionais. Nestes casos, o sucesso é o compilador **recusar-se** a compilar e apresentar uma mensagem de erro semântico clara.

### Testes Base (Requisitos do Guião)
| Teste | Funcionalidade Validada | Resultado |
| :--- | :--- | :--- |
| `ola.pas` | I/O básico e Strings literais | ✅ Sucesso |
| `fatorial.pas` | Recursividade e gestão da pilha de funções | ✅ Sucesso |
| `primo.pas` | Operadores lógicos e aritmética (`mod`) | ✅ Sucesso |
| `array.pas` | Alocação dinâmica e indexação de vetores | ✅ Sucesso |
| `binario.pas` | Manipulação de Strings (`charat`) e conversão | ✅ Sucesso |

### Testes Adicionais (Funcionalidades Extra)
| Teste | Objetivo | Resultado |
| :--- | :--- | :--- |
| `fibonacci.pas` | Lógica sequencial e atualização de variáveis | ✅ Sucesso |
| `soma.pas` | Leitura de input (`readln`) e acumulação | ✅ Sucesso |
| `temperatura.pas` | Precedência de operadores aritméticos | ✅ Sucesso |
| `div.pas` | Distinção semântica entre divisão inteira e real | ✅ Sucesso |

### Testes de Robustez
| Teste | Cenário de Erro | Comportamento do Compilador |
| :--- | :--- | :--- |
| `erro_soma.pas` | Tentativa de somar Inteiro + String | 🛡️ **Bloqueado:** `Erro Semântico` detetado |
| `erro_atribuicao.pas` | Atribuir String a variável Inteira | 🛡️ **Bloqueado:** `Erro Semântico` detetado |
| `erro_div.pas` | Usar `div` com resultado Real | 🛡️ **Bloqueado:** `Erro Semântico` detetado |

---

## 7. Conclusão

O  compilador está funcional e cobre a totalidade do ciclo de tradução, desde a leitura do código fonte até à geração do Assembly. A implementação respeita a arquitetura modular descrita e o sistema comporta-se como esperado nos casos de teste fornecidos e nos cenários de erro criados.