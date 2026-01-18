program ErroSoma;
var 
  resultado: integer;
begin
  { Isto deve falhar: Não se pode somar 10 com texto }
  resultado := 10 + 'Texto';
end.