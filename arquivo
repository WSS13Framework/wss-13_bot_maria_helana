#!/bin/bash

# Define cores para melhor visualização (apenas no terminal)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}🔍 DIAGNÓSTICO DE RSI E LÓGICA DE VENDA${NC}"
echo -e "${BLUE}======================================================${NC}"

CONFIG_FILE="config.py"
STRATEGY_FILE="strategies/rsi_volume_strategy.py"

echo -e "\n${BLUE}--- Verificando 'rsi_overbought' em ${CONFIG_FILE} ---${NC}"
CONFIG_RSI_OVERBOUGHT=$(grep -oP "'rsi_overbought':\s*\K\d+" "${CONFIG_FILE}" 2>/dev/null)

if [ -n "$CONFIG_RSI_OVERBOUGHT" ]; then
    echo -e "${GREEN}✅ Encontrado: 'rsi_overbought': ${CONFIG_RSI_OVERBOUGHT}${NC}"
    if [ "$CONFIG_RSI_OVERBOUGHT" -ne 70 ]; then
        echo -e "${YELLOW}⚠️  AVISO: O valor esperado para 'rsi_overbought' é 70, mas está ${CONFIG_RSI_OVERBOUGHT}.${NC}"
        echo -e "${YELLOW}   👉 Recomenda-se executar o ${GREEN}script_2_fix_config.sh${YELLOW} para corrigir.${NC}"
    else
        echo -e "${GREEN}🎉 'rsi_overbought' está corretamente definido como 70.${NC}"
    fi
else
    echo -e "${RED}❌ ERRO: Não foi possível encontrar 'rsi_overbought' em ${CONFIG_FILE}.${NC}"
    echo -e "${YELLOW}   👉 Verifique o arquivo ${CONFIG_FILE} manualmente.${NC}"
fi

echo -e "\n${BLUE}--- Verificando '_check_sell_conditions' em ${STRATEGY_FILE} ---${NC}"

# Verifica a assinatura do método
if grep -q "def _check_sell_conditions(self, rsi):" "${STRATEGY_FILE}"; then
    echo -e "${RED}❌ Assinatura do método: 'def _check_sell_conditions(self, rsi):' (Falta 'trend').${NC}"
    SIGNATURE_STATUS="INCORRECT"
elif grep -q "def _check_sell_conditions(self, rsi, trend):" "${STRATEGY_FILE}"; then
    echo -e "${GREEN}✅ Assinatura do método: 'def _check_sell_conditions(self, rsi, trend):' (Correta).${NC}"
    SIGNATURE_STATUS="CORRECT"
else
    echo -e "${YELLOW}⚠️  Não foi possível determinar a assinatura de '_check_sell_conditions'.${NC}"
    SIGNATURE_STATUS="UNKNOWN"
fi

# Verifica a chamada do método
if grep -q "self._check_sell_conditions(rsi)" "${STRATEGY_FILE}" && ! grep -q "self._check_sell_conditions(rsi, trend)" "${STRATEGY_FILE}"; then
    echo -e "${RED}❌ Chamada do método: 'self._check_sell_conditions(rsi)' (Falta 'trend').${NC}"
    CALL_STATUS="INCORRECT"
elif grep -q "self._check_sell_conditions(rsi, trend)" "${STRATEGY_FILE}"; then
    echo -e "${GREEN}✅ Chamada do método: 'self._check_sell_conditions(rsi, trend)' (Correta).${NC}"
    CALL_STATUS="CORRECT"
else
    echo -e "${YELLOW}⚠️  Não foi possível determinar a chamada de '_check_sell_conditions'.${NC}"
    CALL_STATUS="UNKNOWN"
fi

    echo -e "${YELLOW}   👉 Recomenda-se executar o ${GREEN}script_3_fix_strategy.sh${YELLOW} para corrigir a estratégia.${NC}"
fi

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}✅ Diagnóstico concluído! Verifique as recomendações acima.${NC}"
echo -e "${BLUE}======================================================${NC}"

if [ "$CONFIG_RSI_OVERBOUGHT" -ne 70 ]; then
    echo -e "${YELLOW}\nPróximo passo recomendado: ${GREEN}script_2_fix_config.sh${NC}"
    echo -e "${YELLOW}\nPróximo passo recomendado: ${GREEN}script_3_fix_strategy.sh${NC}"
else
    echo -e "${GREEN}\nConfiguração e Estratégia parecem corretas. Próximo passo: ${GREEN}script_4_deploy_restart.sh${NC}"
fi
