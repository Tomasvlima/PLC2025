# TPC2
O objetivo deste trabalho é fazer um conversor de MarkDown para HTML, em Python.


# Resolução
[codigo](tp2.py)

Optei por usar a função do Python ```splitLines()``` no input para analizar o texto em Markdown linha a linha numa lista.

resultado = [] é a lista que vai ser convertida para string no final.

Usei uma flag ```ol``` que identifica quando uma lista numerada está aberta ```(<ol>)```, para conseguir identificar quando ainda estou a converter elementos de uma lista ou se já se pode fechar ```(</ol>)```.

Também optei por dividir a resolução do problema em dois passos. Primeiro os elementos mais complexos, como as listas e os cabeçalhos, que afetam parágrafos inteiros. 

Para converter os elementos complexos, usei um ```for loop``` que percorre a lista criada com a função ```splitLines()```, onde cada elemento desta lista é um parágrafo do input em Markdown. 

Em cada iteração do loop, a ordem seguida é esta:
- Começa por ver se é um elemento de uma lista (```re.match(r"\d+\. (.*)", linha)```). Se é um elemento de uma lista faz a respetiva conversão, e se ol = False, adicionámos a abertura de lista em html ```<ol>``` antes do primeiro ```<li>```. Passa à próxima iteração.
- Se o elemento não era de uma lista, mas ol = True, quer dizer que deixou de converter uma lista e por isso tenho que fechar ```</ol>```.
- Se não era elemento de uma lista, verifica se é elemento de cabeçalho (Se for faz a respetiva conversão).
- Se não é nenhum elemento "complexo", adiciona ao resultado sem alterações.

Neste momento, com o loop terminado, ficou por converter os seguintes casos:
- Bold
- Itálico
- Imagens
- Links

Estes casos podem ser tratados num modo "geral", ou seja, converto a lista resultado numa string ```html = ("\n".join(resultado))```, onde posso utilizar ```re.sub```para tratar dos casos que faltam:
- ```html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html)``` -> Bold
- ```html = re.sub(r"\*(.*?)\*", r"<i>\1</i>", html)``` -> Itálico
- ```html = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img src="\2" alt="\1"/>', html)``` -> Imagens
- ```html = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', html)``` -> Links

**Nota:**
Primeiro converte - se as imagens, e depois os links, porque ambas usam a sintaxe ```[texto](url)```. O que distingue um caso do outro, é que as imagens têm um "!" no início.

# Teste
## Input
```
# Exemplo
## Teste 2
### Teste 3
Este é um **exemplo** e este é um *teste*.
1. Primeiro item
2. Segundo item
3. Terceiro item
Como pode ser consultado em [página da UC](http://www.uc.pt) 
Como se vê na imagem seguinte: ![imagem dum coelho](http://www.coellho.com) ...
```
## Output
```
<h1>Exemplo</h1>
<h2>Teste 2</h2>
<h3>Teste 3</h3>
Este é um <b>exemplo</b> e este é um <i>teste</i>.
<ol>
<li>Primeiro item</li>
<li>Segundo item</li>
<li>Terceiro item</li>
</ol>
Como pode ser consultado em <a href="http://www.uc.pt">página da UC</a> 
Como se vê na imagem seguinte: <img src="http://www.coellho.com" alt="imagem dum coelho"/> ...

