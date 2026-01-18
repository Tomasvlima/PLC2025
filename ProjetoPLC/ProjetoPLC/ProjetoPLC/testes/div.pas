program TesteDivisao;
var 
  a, b, resultado: integer;
begin
  writeln('--- Teste de Divisao Inteira ---');
  
  write('Introduza o Numerador: ');
  readln(a);
  
  write('Introduza o Denominador: ');
  readln(b);

  if b = 0 then
    writeln('Erro: Nao e possivel dividir por zero!')
  else
  begin
    resultado := a div b;
    write('Resultado da divisao: ');
    writeln(resultado);
  end;
end.