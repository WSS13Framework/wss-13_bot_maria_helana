#!/bin/bash
set -e

echo "🔧 CORRIGINDO _check_sell_conditions em rsi_volume_strategy.py..."
echo "=================================================="

FILE="strategies/rsi_volume_strategy.py"

# 1. Criar backup
cp "$FILE" "${FILE}.backup_$(date +%s)"
echo "✅ Backup criado: ${FILE}.backup_$(date +%s)"

# 2. Corrigir assinatura
sed -i 's/def _check_sell_conditions(self, rsi):/def _check_sell_conditions(self, rsi, trend):/g' "$FILE"
echo "✅ Assinatura do método corrigida!"

# 3. Validar
if grep -q "def _check_sell_conditions(self, rsi, trend):" "$FILE"; then
    echo "✅ SUCESSO! Método agora aceita 'trend' como parâmetro"
else
    echo "❌ ERRO! Mudança não foi aplicada"
    exit 1
fi

# 4. Mostrar código
echo ""
echo "📝 Código corrigido:"
echo "=================================================="

echo ""
echo "🎉 Execute: bash fix_test_syntax.sh"
