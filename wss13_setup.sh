#!/bin/bash
# wss13_setup.sh - Setup completo WSS+13

echo "🏢 WSS+13 - Setup de Sistema Inteligente"
echo "👨‍💻 Desenvolvido por: Marcos Sea"

# Verificar dependências
echo "🔍 Verificando dependências..."
python3 -c "import ccxt, pandas, talib, rich; print('✅ Todas as libs OK!')" 2>/dev/null || {
    echo "❌ Algumas bibliotecas estão faltando!"
    echo "💡 Execute: pip install ccxt pandas TA-Lib rich"
    exit 1
}

# Configurar API se necessário
if [ ! -f ~/.binance_config ]; then
    echo "⚙️ Configurando API pela primeira vez..."
    if [ -f "./fix_binance_api.sh" ]; then
        ./fix_binance_api.sh
    else
        echo "❌ Script fix_binance_api.sh não encontrado!"
        exit 1
    fi
fi

# Testar sistema completo
echo "🧪 Testando sistema..."
if [ -f "./test_binance_fix.py" ]; then
    python3 test_binance_fix.py
else
    echo "❌ Script test_binance_fix.py não encontrado!"
    exit 1
fi

echo "�� Sistema WSS+13 pronto para ML e automação!"
