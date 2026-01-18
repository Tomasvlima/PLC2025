program FibonacciTest;

var
  n, i, t1, t2, nextTerm: integer;

begin
  writeln('Quantos termos da sequencia de Fibonacci queres?');
  readln(n);

  t1 := 0;
  t2 := 1;

  write('Sequencia: ');
  write(t1);
  write(', ');
  write(t2);

  for i := 3 to n do
  begin
    nextTerm := t1 + t2;
    write(', ');
    write(nextTerm);
    t1 := t2;
    t2 := nextTerm;
  end;

  writeln('');
  writeln('Fim do programa.');
end.