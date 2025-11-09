#!/bin/bash
set -euo pipefail

PROJECT_DIR="/home/sea/Projects/maria-helena-bot"
CONFIG_FILE="$PROJECT_DIR/config.py"
STRATEGY_FILE="$PROJECT_DIR/strategies/rsi_volume_strategy.py"

echo "🔎 Iniciando diagnóstico da estratégia RSI..."
echo "----------------------------------------------"

echo "⚙️ Verificando arquivos essenciais..."
for file in "$CONFIG_FILE" "$STRATEGY_FILE"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ ERRO: Arquivo não encontrado: $file"
        exit 1
    fi
done
echo "✅ Todos os arquivos encontrados."

echo -e "\\n📊 Verificando 'rsi_overbought' em config.py..."

if [[ -n "$CONFIG_RSI_OVERBOUGHT" ]]; then
    echo "✅ Valor de 'rsi_overbought' em config.py: $CONFIG_RSI_OVERBOUGHT"
else
    echo "❌ Não foi possível extrair 'rsi_overbought' de config.py."
fi

echo -e "\\n📋 Verificando assinatura de '_check_sell_conditions'..."
if grep -q "def _check_sell_conditions(self, rsi, trend):" "$STRATEGY_FILE"; then
    echo "✅ Assinatura correta: inclui 'trend'."
else
    echo "❌ Assinatura INCORRETA. 'trend' está ausente."
fi

echo -e "\\n📞 Verificando chamada para '_check_sell_conditions'..."
if grep -q "elif self._check_sell_conditions(rsi, trend):" "$STRATEGY_FILE"; then
    echo "✅ Chamada correta: passa 'trend'."
else
    echo "❌ Chamada INCORRETA. 'trend' está ausente."
fi

echo -e "\\n✅ Diagnóstico concluído."
echo "----------------------------------------------"
