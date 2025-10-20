# TPC3
O objetivo deste trabalho é fazer um analisador léxico para uma linguagem de query com a qual se podem escrever frases do género:
```
# DBPedia: obras de Chuck Berry
select ?nome ?desc where {
?s a dbo:MusicalArtist.
?s foaf:name "Chuck Berry"@en .
?w dbo:artist ?s.
?w foaf:name ?nome.
?w dbo:abstract ?desc
} LIMIT 1000
```

[Resolução](tp3.ipynb)
