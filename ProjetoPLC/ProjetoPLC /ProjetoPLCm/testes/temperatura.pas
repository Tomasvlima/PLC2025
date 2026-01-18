program ConversorTemp;

{ 
  Este programa converte uma temperatura
  de Celsius para Fahrenheit.
  Formula: F = (C * 9) / 5 + 32
}

var
  celsius, fahrenheit: integer;

begin
  writeln('--- Conversor Celsius -> Fahrenheit ---');
  
  { Pede o valor ao utilizador }
  write('Introduza a temperatura em Celsius: ');
  readln(celsius);

  { Inicio do calculo }
  fahrenheit := celsius * 9;
  fahrenheit := fahrenheit div 5; { Atencao: Divisao inteira }
  fahrenheit := fahrenheit + 32;

  write('Temperatura em Fahrenheit: ');
  writeln(fahrenheit);
  
  { Verifica se esta muito quente }
  if fahrenheit > 90 then
    writeln('Uau! Esta muito calor.');
    
  writeln('---------------------------------------');
end.