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
        self.max_position_pct = config['max_position_size']  # 3%
        self.max_daily_loss_pct = config['max_daily_loss']   # 5%
        self.stop_loss_pct = config['stop_loss_pct']         # 2%
        self.max_total_exposure = config.get('max_total_exposure', 0.15)  # 15%
        
        # Estado
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start = datetime.now().date()
        self.open_positions = []
        self.total_trades = 0
        
        # Limites de segurança
        self.max_trades_per_day = config.get('max_trades_per_per_day', 5)
        self.min_time_between_trades = config.get('min_time_between_trades', 300)  # 5 min
        self.last_trade_time = None
        
        logger.info("[green]🛡️  Camada 1: Risk Manager ativado[/green]")
    
    def reset_daily_counters(self):
        """Reset contadores diários à meia-noite"""
        today = datetime.now().date()
        if today != self.daily_start:
            logger.info(f"\n📅 Novo dia! Reset de contadores")
            logger.info(f"   PnL ontem: ${self.daily_pnl:+.2f}")
            logger.info(f"   Trades ontem: {self.daily_trades}")
            
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_start = today
    
    def validate_trade(self, signal, capital):
        """
        VALIDAÇÃO FINANCEIRA - Barreira 1
        
        Returns:
            (bool, str, dict): (aprovado, razão, detalhes)
        """
        self.reset_daily_counters()
        
        details = {
            'capital': capital,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'open_positions': len(self.open_positions)
        }
        
        # REGRA 1: Perda diária máxima
        if self.daily_pnl <= -self.max_daily_loss_pct * capital:
            return False, "🚫 MAX_DAILY_LOSS_ATINGIDO", details
        
        # REGRA 2: Máximo de trades por dia
        if self.daily_trades >= self.max_trades_per_day:
            return False, "🚫 MAX_TRADES_PER_DAY", details
        
        # REGRA 3: Tempo mínimo entre trades
        if self.last_trade_time:
            time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
            if time_since_last < self.min_time_between_trades:
                return False, f"⏰ AGUARDE {int(self.min_time_between_trades - time_since_last)}s", details

        # REGRA 4: Posição já aberta (por enquanto, só 1 por vez)
        if len(self.open_positions) > 0:
            return False, "🔒 POSIÇÃO_JÁ_ABERTA", details
        
        # REGRA 5: Confiança mínima do sinal
        min_confidence = 0.60
        if signal.get('confidence', 0) < min_confidence:
            return False, f"📊 CONFIANÇA_BAIXA ({signal.get('confidence', 0):.2f} < {min_confidence})", details
        
        # REGRA 6: Preço válido
        price = signal.get('price', 0)
        if price <= 0:
            return False, "⚠️  PREÇO_INVÁLIDO", details
        
        # REGRA 7: Exposição total (considerando a nova posição)
        # Esta validação é mais complexa e pode ser feita no OrderManager ou ao tentar abrir a posição
        # Por enquanto, o CashGate já faz uma validação de tamanho de posição.
        # Aqui, podemos verificar se a soma das posições abertas + a nova excederia a exposição total.
        # Para simplificar, vamos deixar essa validação mais granular no CashGate/OrderManager.
        
        # ✅ PASSOU EM TODAS AS VALIDAÇÕES
        return True, "✅ APROVADO", details
    
    def calculate_position_size(self, capital, signal):
        """
        Calcula tamanho da posição baseado em:
        1. Capital disponível
        2. Confiança do sinal
        3. Volatilidade (se disponível)
        4. Performance recente
        """
        base_size = capital * self.max_position_pct
        confidence = signal.get('confidence', 0.7)
        
        # Ajusta por confiança
        # 60% confiança = 60% do tamanho base
        # 80% confiança = 100% do tamanho base
        confidence_factor = min(1.0, (confidence - 0.60) / 0.20)
        adjusted_size = base_size * confidence_factor
        
        # Reduz se teve perdas recentes
        if self.daily_pnl < 0:
            loss_factor = max(0.5, 1 + (self.daily_pnl / capital))  # Max 50% redução
            adjusted_size *= loss_factor
            logger.warning(f"   ⚠️  Reduzindo tamanho por perdas: {loss_factor:.2%}")
        
        return max(adjusted_size, capital * 0.005)  # Mínimo 0.5% do capital para evitar posições muito pequenas
    
    def calculate_stop_loss(self, entry_price, action):
        """
        Calcula stop loss (SEMPRE presente!)
        
        Args:
            entry_price: Preço de entrada
            action: 'BUY' ou 'SELL'
        
        Returns:
            float: Preço do stop loss
        """
        if action == 'BUY':
            stop = entry_price * (1 - self.stop_loss_pct)
        else:  # SELL
            stop = entry_price * (1 + self.stop_loss_pct)
        
        return round(stop, 2)
    
    def calculate_take_profit(self, entry_price, action, risk_reward_ratio=2.0):
        """
        Calcula take profit (reward:risk = 2:1 por padrão)
        """
        stop_distance = entry_price * self.stop_loss_pct
        profit_distance = stop_distance * risk_reward_ratio
        
        if action == 'BUY':
            take_profit = entry_price + profit_distance
        else:  # SELL
            take_profit = entry_price - profit_distance
        
        return round(take_profit, 2)
    
    def open_position(self, entry_price, size, stop_loss, take_profit, action):
        """Registra abertura de posição"""
        position = {
            'entry_price': entry_price,
            'size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'action': action,
            'entry_time': datetime.now(),
            'pnl': 0.0
        }
        
        self.open_positions.append(position)
        self.daily_trades += 1
        self.total_trades += 1
        self.last_trade_time = datetime.now()
        
        logger.info(f"[green]✅ Posição aberta #{self.total_trades}[/green]")
        return position
    
    def close_position(self, exit_price, exit_type='SIGNAL'):
        """Fecha posição e atualiza métricas"""
        if not self.open_positions:
            return None
        
        position = self.open_positions.pop(0) # Assume FIFO (First-In, First-Out)
        
        # Calcula PnL
        if position['action'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * position['size']
        else:  # SELL
            pnl = (position['entry_price'] - exit_price) * position['size']
        
        self.daily_pnl += pnl
        
        # Log
        emoji = "��" if pnl > 0 else "🔴"
        logger.info(f"{emoji} Posição fechada: ${pnl:+.2f} ({exit_type})")
        
        return {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'exit_type': exit_type,
            'pnl': pnl,
            'return_pct': (pnl / (position['entry_price'] * position['size'])) * 100 if (position['entry_price'] * position['size']) != 0 else 0
        }
    
    def check_stop_loss(self, current_price):
        """Verifica se stop loss foi atingido"""
        if not self.open_positions:
            return False
        
        position = self.open_positions[0]
        
        if position['action'] == 'BUY' and current_price <= position['stop_loss']:
            logger.warning(f"[red]🛑 STOP LOSS atingido! ${current_price} <= ${position['stop_loss']}[/red]")
            return True
        
        elif position['action'] == 'SELL' and current_price >= position['stop_loss']:
            logger.warning(f"[red]🛑 STOP LOSS atingido! ${current_price} >= ${position['stop_loss']}[/red]")
            return True
        
        return False
    
    def check_take_profit(self, current_price):
        """Verifica se take profit foi atingido"""
        if not self.open_positions:
            return False
        
        position = self.open_positions[0]
        
        if position['action'] == 'BUY' and current_price >= position['take_profit']:
            logger.info(f"[green]🎯 TAKE PROFIT atingido! ${current_price} >= ${position['take_profit']}[/green]")
            return True
        
        elif position['action'] == 'SELL' and current_price <= position['take_profit']:
            logger.info(f"[green]🎯 TAKE PROFIT atingido! ${current_price} <= ${position['take_profit']}[/green]")
            return True
        
        return False
    
    def _calculate_total_exposure(self):
        """Calcula exposição total atual (soma dos tamanhos das posições abertas)"""
        if not self.open_positions:
            return 0.0
        
        # Isso é uma simplificação. A exposição real seria o valor em moeda de cotação.
        # Aqui, estamos somando o 'size' que é a quantidade da moeda base.
        # Para uma exposição precisa, precisaríamos do preço atual de cada posição.
        total = sum(pos['size'] for pos in self.open_positions)
        return total
    
    def get_status(self):
        """Status do risk manager"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'total_trades': self.total_trades,
            'open_positions': len(self.open_positions),
            'can_trade': self.daily_pnl > -self.max_daily_loss_pct and self.daily_trades < self.max_trades_per_day
        }
