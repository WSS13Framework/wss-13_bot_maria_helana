#!/bin/bash
echo "🔑 Configurando API Binance..."

cat > ~/.binance_config << 'INNER_EOF'
# Configuração Binance API
BINANCE_API_KEY="sua_api_key_aqui"
BINANCE_SECRET_KEY="sua_secret_key_aqui"
BINANCE_TESTNET=false
INNER_EOF

echo "📝 Arquivo de configuração criado em ~/.binance_config"
echo "⚠️  EDITE o arquivo com suas credenciais reais!"
echo "📖 Para editar: nano ~/.binance_config"
