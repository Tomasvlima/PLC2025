program SomaAteN;
var
  i, n, soma: integer;
begin
  writeln('--- Programa Soma Ate N ---');
  write('Introduza o valor de N: ');
  readln(n);

  soma := 0;
  for i := 1 to n do
    soma := soma + i;

  writeln('--- Resultado ---');
  write('A soma de 1 ate ');
  write(n);
  write(' e: ');
  writeln(soma);
  writeln('-----------------');
end.