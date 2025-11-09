#!/bin/bash

# Define cores para melhor visualização (apenas no terminal)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}🔧 CORRIGINDO 'rsi_overbought' em config.py${NC}"
echo -e "${BLUE}======================================================${NC}"

CONFIG_FILE="config.py"
BACKUP_FILE="${CONFIG_FILE}.bak.$(date +%Y%m%d%H%M%S)"

echo -e "\n${BLUE}--- Criando backup de ${CONFIG_FILE} ---${NC}"
cp "${CONFIG_FILE}" "${BACKUP_FILE}"
echo -e "${GREEN}✅ Backup criado: ${BACKUP_FILE}${NC}"

echo -e "\n${BLUE}--- ANTES da correção: ${CONFIG_FILE} ---${NC}"

echo -e "\n${BLUE}--- Aplicando correção: Definindo 'rsi_overbought' para 70 ---${NC}"
# Expressão regular para encontrar a linha e substituir o valor numérico
# Garante que substitui APENAS o número da linha 'rsi_overbought'
sed -i -E "s/('rsi_overbought':\s*)[0-9]+(,.*)/\170\2/" "${CONFIG_FILE}"

echo -e "\n${BLUE}--- DEPOIS da correção: ${CONFIG_FILE} ---${NC}"

# Verificar o resultado
CONFIG_RSI_OVERBOUGHT=$(grep -oP "'rsi_overbought':\s*\K\d+" "${CONFIG_FILE}" 2>/dev/null)
if [ -n "$CONFIG_RSI_OVERBOUGHT" ] && [ "$CONFIG_RSI_OVERBOUGHT" -eq 70 ]; then
    echo -e "${GREEN}🎉 'rsi_overbought' em config.py agora é 70!${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${YELLOW}\nPróximo passo recomendado: ${GREEN}script_3_fix_strategy.sh${NC}"
else
    echo -e "${RED}❌ ERRO: Não foi possível definir 'rsi_overbought' para 70. Verifique ${CONFIG_FILE} manualmente.${NC}"
    echo -e "${BLUE}======================================================${NC}"
fi
