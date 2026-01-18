if [ -z "$1" ]; then
    echo "Uso: ./run.sh testes/ficheiro.pas"
    exit 1
fi

INPUT=$1
OUTPUT="${INPUT%.pas}.vm"

# 1. Limpa o ficheiro de entrada (tira \r do Pascal)
sed -i 's/\r$//' "$INPUT"

# 2. Compila
python3 src/parser.py "$INPUT"

# 3. Verifica erro
if [ $? -ne 0 ]; then
    echo "❌ Erro na compilação."
    exit 1
fi

# 4. LIMPEZA NUCLEAR DO OUTPUT (Remove \r à força)
tr -d '\r' < "$OUTPUT" > "$OUTPUT.tmp" && mv "$OUTPUT.tmp" "$OUTPUT"

echo ""
echo "✅ Sucesso! Ficheiro limpo gerado em: $OUTPUT"
echo "Podes fazer upload agora."