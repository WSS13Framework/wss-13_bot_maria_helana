#!/bin/bash

echo "🔧 Corrigindo erro 'bool is not callable'..."

# 1. Atualizar CircuitBreaker
sed -i '/def is_tripped(self):/,+2d' protection/circuit_breaker.py

# 2. Corrigir chamada no bot.py
sed -i 's/self.circuit_breaker.is_tripped()/self.circuit_breaker.is_tripped/g' bot.py

echo "✅ Correção aplicada!"
echo "🔄 Execute o bot novamente com: python bot.py"

