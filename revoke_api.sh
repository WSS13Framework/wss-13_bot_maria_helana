#!/bin/bash
echo "🔒 Revogando API e limpando configurações..."

# Limpar arquivo de configuração
rm -f ~/.binance_config

# Criar configuração vazia
cat > ~/.binance_config << 'INNER_EOF'
# Configuração Binance API - WSS+13
BINANCE_API_KEY="sua_api_key_aqui"
BINANCE_SECRET_KEY="sua_secret_key_aqui"
BINANCE_TESTNET=true
INNER_EOF

echo "✅ Configurações limpas!"
echo "🌐 Não esqueça de revogar a API em: https://www.binance.com/en/my/settings/api-management"
