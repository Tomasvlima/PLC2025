# Trabalho Prático 2

## Resumo
O objetivo deste trabalho prático foi criar em Python um pequeno conversor de Markdown para HTML para os seguintes elementos descritivos na "Basic Syntax" da Cheat Sheet:

* Cabeçalhos: linhas iniciadas por "# texto", ou "## texto" ou "### texto";
* Bold: pedaços de texto entre "**";
* Itálico: pedaços de texto entre "*";
* Lista numerada;
* Link: [texto ](endereço URL);
* Imagem: ![texto alternativo](path para a imagem).

O meu raciocínio passou por identificar, linha a linha, quais correspondiam a cabeçalhos, usando re.match, convertê-los para HTML e acrescentar o resultado a uma lista resultado, que guarda todos os blocos do texto. 
Segui o mesmo raciocínio para as linhas que fossem itens de lista. Para estes elementos descritivos usei uma variável lista_itens, que guarda todos os itens da lista já convertidos para HTML. Quando a lista termina, envolvo os elementos de lista_itens e adiciono tudo à lista resultado.
Por fim, para tratar as formatações inline restantes (negrito, itálico, links, imagens), criei a função converter_inline, que é aplicada a cada linha no momento certo, garantindo que o texto fica corretamente formatado em HTML.


## Lista de Resultados
- [Notebook com a solução do TP2](tp2.ipynb)
