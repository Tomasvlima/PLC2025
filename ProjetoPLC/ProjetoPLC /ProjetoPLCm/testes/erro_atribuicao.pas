program ErroAtribuicao;
var 
  numero: integer;
begin
  { Isto deve falhar porque 'numero' é INTEGER e 'Ola' é STRING }
  numero := 'Ola Mundo';
end.