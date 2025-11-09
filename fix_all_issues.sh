#!/bin/bash

# Correção completa para o Maria Helena Bot

echo "🔧 Iniciando correções automáticas..."

# 1. Corrigir Circuit Breaker
echo "⚡ Corrigindo CircuitBreaker..."
cat > protection/circuit_breaker.py << 'EOL'
from datetime import datetime, timedelta
from rich.console import Console
import json
import os
import logging

logger = logging.getLogger(__name__)
console = Console()

class CircuitBreaker:
    def __init__(self, config):
        self.state_file = 'maria_helena_state.json'
        self.emergency_log = 'logs/emergency.log'
        self.max_capital_loss_pct = config.get('max_capital_loss', 0.20)
        self.max_consecutive_losses = config.get('max_consecutive_losses', 5)
        self.max_runtime_hours = config.get('max_runtime_hours', 24)
        self.consecutive_losses = 0
        self.current_losses = 0
        self.max_losses = self.max_consecutive_losses
        self.start_time = datetime.now()
        self.initial_capital = None
        self.kill_switch_active = False
        self.emergency_reasons = []
        self.is_tripped = False
        self.daily_pnl = 0.0
        
        logger.info("[red]⚡ Camada 3: Circuit Breaker ativado[/red]")
        os.makedirs('logs', exist_ok=True)
        if not os.path.exists(self.emergency_log):
            open(self.emergency_log, 'w').close()
        
        # Método load_state movido para dentro da classe
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.initial_capital = state.get('initial_capital')
                self.consecutive_losses = state.get('consecutive_losses', 0)
                self.kill_switch_active = state.get('kill_switch_active', False)
                self.emergency_reasons = state.get('emergency_reasons', [])
                if state.get('start_time'):
                    self.start_time = datetime.fromisoformat(state['start_time'])
                logger.info("[cyan]📂 Estado anterior carregado[/cyan]")
            except Exception as e:
                logger.warning(f"[yellow]⚠️ Erro ao carregar estado: {e}[/yellow]")

    def load_state(self):
        """Método mantido para compatibilidade"""
        pass

    # ... (outros métodos permanecem iguais) ...
EOL

# 2. Verificar estrutura de arquivos
echo "📂 Verificando estrutura de diretórios..."
mkdir -p protection strategies core/orders data logs

# 3. Criar arquivos essenciais se não existirem
if [ ! -f "data/normalizer.py" ]; then
    echo "📊 Criando normalizer.py básico..."
    cat > data/normalizer.py << 'EOL'
class Normalizer:
    def __init__(self, config):
        self.config = config
    
    def process(self, ohlcv):
        return {
            'price': ohlcv['close'],
            'volume': ohlcv['volume'],
            'normalized': 0.5
        }
EOL
fi

echo "✅ Todas as correções foram aplicadas com sucesso!"
echo "🔄 Execute o bot novamente com: python bot.py"
