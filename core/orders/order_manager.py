# core/orders/order_manager.py

import ccxt # type: ignore
import logging
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

# Importar módulos de proteção
from protection.risk_manager import RiskManager
from protection.technical_guard import TechnicalGuard
from protection.circuit_breaker import CircuitBreaker
from protection.cash_gate.cash_gate import CashGate

# Configurações do bot (do config.py)
from config import CONFIG

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrderManager:
    """
    Gerencia todas as interações de ordem com a exchange.
    Implementa o "Cash Gate" como primeira linha de defesa antes de qualquer execução.
    """

    def __init__(self, exchange: ccxt.Exchange, risk_manager: RiskManager, 
                 technical_guard: TechnicalGuard, circuit_breaker: CircuitBreaker,
                 cash_gate: CashGate):
        
        self.exchange = exchange
        self.risk_manager = risk_manager
        self.technical_guard = technical_guard
        self.circuit_breaker = circuit_breaker
        self.cash_gate = cash_gate  # Nova dependência
        
        self.symbol = CONFIG['SYMBOL']
        # O OrderManager não mantém seu próprio current_capital, ele consulta o CashGate
        
        logger.info("OrderManager inicializado.")

    def _can_execute_trade(self, signal: Dict[str, Any], amount_in_quote_currency: float) -> Tuple[bool, str]:
        """
        Implementa o "Cash Gate" como a primeira linha de defesa.
        Verifica todas as condições de segurança antes de permitir uma ordem.
        amount_in_quote_currency: O valor total da ordem na moeda de cotação (ex: USDT).
        """
        logger.info(f"Cash Gate: Verificando sinal para {signal.get('action')} {signal.get('symbol')} com valor {amount_in_quote_currency:.2f}")

        # 1. Verificação do Circuit Breaker (Prioridade Máxima)
        can_continue, cb_reason = self.circuit_breaker.should_continue()
        if not can_continue:
            logger.warning(f"Cash Gate REJEITADO: Circuit Breaker ativo. Razão: {cb_reason}")
            return False, f"Circuit Breaker ativo: {cb_reason}"

        # 2. Verificação de Conexão e Dados Técnicos
        api_ok, api_reason = self.technical_guard.validate_api_connection(self.exchange)
        if not api_ok:
            logger.warning(f"Cash Gate REJEITADO: Falha na conexão com a exchange. Razão: {api_reason}")
            return False, f"Conexão com exchange falhou: {api_reason}"
        
        # (Futuro) Adicionar validação de dados de mercado mais recentes aqui
        # Ex: ticker_ok, ticker_reason, _ = self.technical_guard.validate_ticker_data(latest_ticker)
        # if not ticker_ok: ...

        # 3. Validação Financeira pelo Risk Manager
        # O RiskManager precisa do capital atual do bot, que vem do CashGate
        rm_approved, rm_reason, rm_details = self.risk_manager.validate_trade(signal, self.cash_gate.current_capital)
        if not rm_approved:
            logger.warning(f"Cash Gate REJEITADO: Risk Manager não aprovou. Razão: {rm_reason}. Detalhes: {rm_details}")
            return False, f"Risk Manager rejeitou: {rm_reason}"

        # 4. Validação de Alocação de Capital pelo Cash Gate (agora com regras de negócio!)
        cg_approved, cg_reason = self.cash_gate.can_reserve(amount_in_quote_currency)
        if not cg_approved:
            logger.warning(f"Cash Gate REJEITADO: Cash Gate não aprovou alocação. Razão: {cg_reason}")
            return False, f"Cash Gate rejeitou: {cg_reason}"

        logger.info("Cash Gate APROVADO: Condições de segurança atendidas.")
        return True, "Cash Gate APROVADO"

    def execute_order(self, action: str, amount: float, price: float, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Executa uma ordem após validação do Cash Gate.
        
        Args:
            action: 'BUY' ou 'SELL'
            amount: Quantidade na moeda base (ex: BTC)
            price: Preço atual
            signal: Dicionário com informações do sinal
            
        Returns:
            Dicionário com detalhes da ordem ou None se falhar
        """
        symbol = signal.get('symbol', self.symbol)
        
        if not price or price <= 0:
            logger.error("Preço inválido para execução de ordem.")
            return None

        # Calcula valor total em moeda de cotação (USDT)
        amount_in_quote_currency = amount * price
        
        if amount_in_quote_currency <= 0:
            logger.error("Valor da ordem é zero ou negativo. Abortando.")
            return None

        # Validação pelo Cash Gate
        approved, reason = self._can_execute_trade(signal, amount_in_quote_currency)
        if not approved:
            logger.error(f"Ordem rejeitada: {reason}")
            return None
        
        # Reserva os fundos
        if not self.cash_gate.reserve(amount_in_quote_currency):
            logger.error(f"Falha ao reservar fundos: {amount_in_quote_currency:.2f}")
            return None

        order_type = 'market'
        
        logger.info(f"Executando ordem {action} de {amount:.8f} {symbol} @ {price:.2f} (total: {amount_in_quote_currency:.2f})")
        
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=action.lower(),
                amount=amount,
            )
            
            logger.info(f"✅ Ordem executada: {order}")
            
            # Commit da reserva
            executed_cost = float(order.get('cost', amount_in_quote_currency))
            self.cash_gate.commit(executed_cost)

            # Registra posição no RiskManager
            entry_price = float(order.get('price', price))
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, action)
            take_profit = self.risk_manager.calculate_take_profit(entry_price, action)
            
            self.risk_manager.open_position(
                entry_price=entry_price,
                size=amount,
                stop_loss=stop_loss,
                take_profit=take_profit,
                action=action
            )
            
            return order

        except ccxt.NetworkError as e:
            logger.error(f"Erro de rede: {e}")
            self.cash_gate.release(amount_in_quote_currency)
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Erro da exchange: {e}")
            self.cash_gate.release(amount_in_quote_currency)
            return None
        except Exception as e:
            logger.error(f"Erro desconhecido: {e}")
            self.cash_gate.release(amount_in_quote_currency)
            return None

    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        MÉTODO LEGADO - Mantido para compatibilidade.
        Use execute_order() para novas implementações.
        """
        action = signal.get('action')
        symbol = signal.get('symbol', self.symbol)
        price = signal.get('price')
        
        if not price or price <= 0:
            return {"status": "rejected", "reason": "Preço inválido"}

        amount_in_quote_currency = self.risk_manager.calculate_position_size(
            self.cash_gate.current_capital, 
            signal
        )
        
        if amount_in_quote_currency <= 0:
            return {"status": "rejected", "reason": "Tamanho de posição inválido"}

        amount_base_currency = amount_in_quote_currency / price
        
        order = self.execute_order(action, amount_base_currency, price, signal)
        
        if order:
            return {"status": "executed", "order": order}
        else:
            return {"status": "failed", "reason": "Falha na execução"}

    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Busca o status de uma ordem na exchange."""
        try:
            status = self.exchange.fetch_order(order_id, symbol)
            return status
        except Exception as e:
            logger.error(f"Erro ao buscar status da ordem {order_id}: {e}")
            return {"status": "error", "reason": str(e)}

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancela uma ordem pendente na exchange."""
        try:
            canceled_order = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Ordem {order_id} cancelada: {canceled_order}")
            return canceled_order
        except Exception as e:
            logger.error(f"Erro ao cancelar ordem {order_id}: {e}")
            return {"status": "error", "reason": str(e)}

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Busca todas as ordens abertas na exchange."""
        try:
            open_orders = self.exchange.fetch_open_orders(symbol)
            return open_orders
        except Exception as e:
            logger.error(f"Erro ao buscar ordens abertas: {e}")
            return []

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Verifica a posição atual para um símbolo."""
        try:
            balance = self.exchange.fetch_balance()
            base_currency = symbol.split('/')[0]
            if base_currency in balance['total']:
                return {'symbol': symbol, 'amount': balance['total'][base_currency]}
            return {'symbol': symbol, 'amount': 0}
        except Exception as e:
            logger.error(f"Erro ao buscar posição para {symbol}: {e}")
            return {'symbol': symbol, 'amount': 0, 'error': str(e)}

    def get_position_info(self) -> Dict[str, Any]:
        """Retorna informações da posição atual do RiskManager."""
        return {
            'is_in_position': self.risk_manager.is_in_position,
            'entry_price': self.risk_manager.entry_price,
            'amount': self.risk_manager.position_size,
            'stop_loss': self.risk_manager.stop_loss,
            'take_profit': self.risk_manager.take_profit
        }