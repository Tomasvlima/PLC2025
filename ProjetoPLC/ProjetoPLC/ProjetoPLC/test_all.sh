# Cores para o output ficar bonito
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}    A EXECUTAR BATERIA DE TESTES PRO     ${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""

# Contadores
PASS=0
FAIL=0

# Percorre todos os ficheiros .pas na pasta testes
for file in testes/*.pas; do
    filename=$(basename "$file")
    
    # 1. Verificar se é um teste de ERRO (deve falhar)
    if [[ $filename == erro_* ]]; then
        echo -n -e "Testando GUARDAS em ${YELLOW}$filename${NC}: "
        # Executa e guarda o output, ignorando o ficheiro .vm gerado se houver erro
        out=$(./run.sh "$file" 2>&1)
        exit_code=$?

        if [ $exit_code -ne 0 ]; then
            # Se deu erro (exit code != 0), é SUCESSO para nós!
            echo -e "${GREEN}✅ SUCESSO (O compilador barrou o erro corretamente)${NC}"
            PASS=$((PASS+1))
        else
            # Se não deu erro, FALHOU o teste
            echo -e "${RED}❌ FALHA (O compilador deixou passar o erro!)${NC}"
            FAIL=$((FAIL+1))
        fi

    # 2. Verificar se é um teste NORMAL (deve passar)
    else
        echo -n -e "Compilando ${NC}$filename${NC}: "
        out=$(./run.sh "$file" 2>&1)
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            # Se deu 0, compilou bem
            echo -e "${GREEN}✅ SUCESSO${NC}"
            PASS=$((PASS+1))
        else
            # Se deu erro, FALHOU
            echo -e "${RED}❌ FALHA NA COMPILAÇÃO${NC}"
            echo "$out" # Mostra o erro para saberes o que foi
            FAIL=$((FAIL+1))
        fi
    fi
done

echo ""
echo -e "${YELLOW}=========================================${NC}"
echo -e "Resumo Final:"
echo -e "${GREEN}Passaram: $PASS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Falharam: $FAIL${NC}"
else
    echo -e "${GREEN}Falharam: 0 (Tudo perfeito!)${NC}"
fi
echo -e "${YELLOW}=========================================${NC}"