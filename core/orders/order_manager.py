# core/orders/order_manager.py

import ccxt
import logging
from datetime import datetime

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
        self.cash_gate = cash_gate # Nova dependência
        
        self.symbol = CONFIG['symbol']
        # O OrderManager não mantém seu próprio current_capital, ele consulta o CashGate
        
        logger.info("OrderManager inicializado.")

    def _can_execute_trade(self, signal: dict, amount_in_quote_currency: float) -> (bool, str):
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

    def execute_trade(self, signal: dict) -> dict:
        """
        Tenta executar um trade após passar pelo Cash Gate.
        Retorna os detalhes da ordem executada ou um erro.
        """
        action = signal.get('action') # 'BUY' ou 'SELL'
        symbol = signal.get('symbol', self.symbol)
        price = signal.get('price') # Preço de entrada sugerido
        
        if not price or price <= 0:
            logger.error("Preço do sinal inválido para execução de trade.")
            return {"status": "rejected", "reason": "Preço do sinal inválido"}

        # Calcular o valor total da posição na moeda de cotação (ex: USDT)
        # O RiskManager calcula o tamanho da posição com base no capital do CashGate
        amount_in_quote_currency = self.risk_manager.calculate_position_size(self.cash_gate.current_capital, signal)
        
        if amount_in_quote_currency <= 0:
            logger.error("Tamanho da posição calculado é zero ou negativo. Abortando trade.")
            return {"status": "rejected", "reason": "Tamanho da posição inválido"}

        # --- Validação e Reserva de Fundos pelo CashGate ---
        approved, reason = self._can_execute_trade(signal, amount_in_quote_currency)
        if not approved:
            logger.error(f"Não foi possível executar trade: {reason}")
            return {"status": "rejected", "reason": reason}
        
        # Se aprovado, efetivamente reserva os fundos no CashGate
        if not self.cash_gate.reserve(amount_in_quote_currency):
            logger.error(f"Falha inesperada ao reservar fundos no CashGate para {amount_in_quote_currency:.2f}.")
            return {"status": "rejected", "reason": "Falha interna ao reservar fundos."}
        # --- Fim Validação e Reserva ---

        # Para ordens de COMPRA (BUY), o 'amount' no CCXT é a quantidade da moeda base (ex: BTC) que você quer comprar.
        # Para ordens de VENDA (SELL), o 'amount' é a quantidade da moeda base (ex: BTC) que você quer vender.
        # Se amount_in_quote_currency é o valor em USDT, precisamos converter para a quantidade da moeda base.
        amount_base_currency = amount_in_quote_currency / price
        
        order_type = 'market' # Usamos ordem de mercado inicialmente
        
        logger.info(f"Executando ordem de {action} {amount_base_currency:.8f} {symbol} (valor: {amount_in_quote_currency:.2f}) via {order_type}...")
        
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=action.lower(), # 'buy' ou 'sell'
                amount=amount_base_currency, # Quantidade da moeda base (ex: BTC)
            )
            
            logger.info(f"Ordem executada com sucesso: {order}")
            
            # --- Commit da Reserva no CashGate ---
            # O valor real gasto pode ser ligeiramente diferente devido ao slippage em ordens de mercado.
            # Idealmente, você obteria o 'cost' (valor total em moeda de cotação) da ordem executada.
            # Por enquanto, vamos usar o valor que tentamos alocar.
            # Em um sistema mais avançado, você buscaria o 'filled' amount e 'cost' da ordem.
            executed_cost = float(order.get('cost') or amount_in_quote_currency)
            self.cash_gate.commit(executed_cost)
            # --- Fim Commit ---

            # Registrar a abertura da posição no RiskManager
            entry_price = float(order.get('price') or signal.get('price')) # Usar preço da ordem ou do sinal
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, action)
            take_profit = self.risk_manager.calculate_take_profit(entry_price, action)
            
            self.risk_manager.open_position(
                entry_price=entry_price,
                size=amount_base_currency, # Tamanho da posição na moeda base
                stop_loss=stop_loss,
                take_profit=take_profit,
                action=action
            )
            
            return {"status": "executed", "order": order}

        except ccxt.NetworkError as e:
            logger.error(f"Erro de rede ao executar ordem: {e}")
            self.cash_gate.release(amount_in_quote_currency) # Libera a reserva se a ordem falhou
            return {"status": "failed", "reason": f"Network Error: {e}"}
        except ccxt.ExchangeError as e:
            logger.error(f"Erro da exchange ao executar ordem: {e}")
            self.cash_gate.release(amount_in_quote_currency) # Libera a reserva se a ordem falhou
            return {"status": "failed", "reason": f"Exchange Error: {e}"}
        except Exception as e:
            logger.error(f"Erro desconhecido ao executar ordem: {e}")
            self.cash_gate.release(amount_in_quote_currency) # Libera a reserva se a ordem falhou
            return {"status": "failed", "reason": f"Unknown Error: {e}"}

    def get_order_status(self, order_id: str, symbol: str) -> dict:
        """Busca o status de uma ordem na exchange."""
        try:
            status = self.exchange.fetch_order(order_id, symbol)
            return status
        except Exception as e:
            logger.error(f"Erro ao buscar status da ordem {order_id}: {e}")
            return {"status": "error", "reason": str(e)}

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        """Cancela uma ordem pendente na exchange."""
        try:
            canceled_order = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Ordem {order_id} cancelada: {canceled_order}")
            # Se uma ordem for cancelada, a reserva deve ser liberada
            # Isso requer que o OrderManager saiba o valor reservado para aquela ordem específica
            # Para simplificar, assumimos que o CashGate gerencia reservas de forma agregada.
            # Em um sistema real, você teria um mapeamento order_id -> reserved_amount.
            return canceled_order
        except Exception as e:
            logger.error(f"Erro ao cancelar ordem {order_id}: {e}")
            return {"status": "error", "reason": str(e)}

    def get_open_orders(self, symbol: str = None) -> list:
        """Busca todas as ordens abertas na exchange."""
        try:
            open_orders = self.exchange.fetch_open_orders(symbol)
            return open_orders
        except Exception as e:
            logger.error(f"Erro ao buscar ordens abertas: {e}")
            return []

    def get_position(self, symbol: str) -> dict:
        """Verifica a posição atual para um símbolo."""
        try:
            balance = self.exchange.fetch_balance()
            # Exemplo para BTC/USDT, buscaria o balanço de BTC
            base_currency = symbol.split('/')[0]
            if base_currency in balance['total']:
                return {'symbol': symbol, 'amount': balance['total'][base_currency]}
            return {'symbol': symbol, 'amount': 0}
        except Exception as e:
            logger.error(f"Erro ao buscar posição para {symbol}: {e}")
            return {'symbol': symbol, 'amount': 0, 'error': str(e)}

    def update_current_capital(self, new_capital: float):
        """
        Este método não é mais necessário, pois o CashGate é a fonte da verdade do capital.
        O OrderManager deve consultar o CashGate para o capital.
        """
        logger.warning("OrderManager.update_current_capital() chamado, mas o capital é gerenciado pelo CashGate.")
