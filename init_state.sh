
#!/bin/bash

echo "🔄 Inicializando arquivos de estado..."

# Criar diretórios se não existirem
mkdir -p state logs

# Arquivo de estado principal
if [ ! -f "state/maria_helena_state.json" ]; then
    cat > state/maria_helena_state.json << 'EOL'
{
    "last_trade": null,
    "capital": 1000.0,
    "open_positions": [],
    "daily_pnl": 0.0
}
EOL
    echo "✅ state/maria_helena_state.json criado"
fi

# Arquivo do Circuit Breaker
if [ ! -f "state/circuit_breaker.json" ]; then
    cat > state/circuit_breaker.json << 'EOL'
{
    "consecutive_losses": 0,
    "is_tripped": false,
    "emergency_reasons": []
}
EOL
    echo "✅ state/circuit_breaker.json criado"
fi

echo "🎉 Estado inicial configurado com sucesso!"

