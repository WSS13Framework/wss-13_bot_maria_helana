# protection/risk_manager.py

from datetime import datetime, timedelta
from rich.console import Console
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

console = Console()

class RiskManager:
    """
    Gestor de Risco - PRIMEIRA CAMADA DE PROTEÇÃO
    
    Regras INEGOCIÁVEIS:
    1. Stop loss SEMPRE presente
    2. Perda diária máxima NUNCA excedida
    3. Tamanho de posição SEMPRE calculado
    4. Exposição total SEMPRE monitorada
    """
    
    def __init__(self, config):
        self.max_position_pct = config['MAX_POSITION_SIZE']  # 3%
        self.max_daily_loss_pct = config['MAX_DAILY_LOSS']   # 5%
        self.stop_loss_pct = config['STOP_LOSS']         # 2%
        self.max_total_exposure = config.get('MAX_TOTAL_EXPOSURE', 0.15)  # 15%
        
        # Estado
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start = datetime.now().date()
        self.open_positions = []
        self.total_trades = 0
        
        # Limites de segurança
        self.max_trades_per_day = config.get('MAX_TRADES_PER_DAY', 5)
        self.min_time_between_trades = config.get('MIN_TIME_BETWEEN_TRADES', 300)  # 5 min
        self.last_trade_time = None

        # Atributos adicionais necessários
        self.is_in_position = False
        self.entry_price = 0.0
        self.position_size = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        
        logger.info("[green]🛡️  Camada 1: Risk Manager ativado[/green]")
    
    # ... (mantenha todos os outros métodos existentes) ...