#!/usr/bin/env python3
# ARQUIVO: maria_helena_estrategista.py
# FUNÇÃO NO ECOSSISTEMA MARIA HELENA:
# Este é o "Estrategista". Sua função é executar a lógica de trading.
# Ele consome dados de mercado em tempo real, aplica uma estratégia
# (ex: RSIVolumeStrategy) e, se as condições forem atendidas e as
# camadas de proteção permitirem, decide sobre a execução de ordens
# de compra ou venda. Ele é o tomador de decisão do ecossistema.

"""
🤖 MARIA HELENA Trading Bot v0.2
"""
# Standard library imports
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import os
import sys

# Third-party imports
import ccxt  # type: ignore
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

# Local imports
from config import CONFIG  # Ensure CONFIG is imported after load_dotenv
from protection.risk_manager import RiskManager
from protection.technical_guard import TechnicalGuard
from protection.circuit_breaker import CircuitBreaker
from strategies.mentor_signal_processor import MentorSignalProcessor
from data.normalizer import Normalizer
from strategies.rsi_volume_strategy import RSIVolumeStrategy
from protection.cash_gate.cash_gate import CashGate
from core.orders.order_manager import OrderManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("maria_helena_bot.log"),
        logging.StreamHandler(sys.stdout)  # Also output to console
    ]
)
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console()


class MariaHelenaBot:
    """
    Bot de trading automatizado com múltiplas camadas de proteção.
    
    Características:
    - Estratégia RSI + Volume
    - Proteção de risco (RiskManager)
    - Circuit Breaker para perdas consecutivas
    - Cash Gate para validação de ordens
    - Modo Mentor para aprendizado
    """
    
    def __init__(self, config: Dict[str, Any] = CONFIG):
        """
        Inicializa o bot com todas as configurações, proteções e estratégias.
        
        Args:
            config (Dict[str, Any]): Dicionário de configurações do bot.
        """
        self.config: Dict[str, Any] = config
        
        self.exchange_name: str = config['EXCHANGE']
        self.symbol: str = config['SYMBOL']
        self.timeframe: str = config['TIMEFRAME']
        self.mentor_mode: bool = config['MENTOR_MODE']
        self.live_mode: bool = config['LIVE_MODE']
        self.check_interval: int = config['CHECK_INTERVAL']
        
        self.capital: float = config['INITIAL_CAPITAL']  # Initial capital for tracking purposes
        self.current_balance: float = self.capital  # This would be updated from exchange for live trading

        self.exchange = self._initialize_exchange()
        
        # Initialize protection modules
        self.risk_manager: RiskManager = RiskManager(self.config)
        self.technical_guard: TechnicalGuard = TechnicalGuard()
        self.circuit_breaker: CircuitBreaker = CircuitBreaker(self.config)
        self.cash_gate: CashGate = CashGate(self.config["INITIAL_CAPITAL"])
        
        # Initialize data and strategy modules
        self.normalizer: Normalizer = Normalizer(self.config)
        self.strategy: RSIVolumeStrategy = RSIVolumeStrategy(self.config)
        
        self.mentor_processor: Optional[MentorSignalProcessor] = None
        if self.mentor_mode:
            self.mentor_processor = MentorSignalProcessor()

        # Initialize order management
        self.order_manager: OrderManager = OrderManager(
            self.exchange, 
            self.risk_manager, 
            self.technical_guard, 
            self.circuit_breaker, 
            self.cash_gate
        )

        self._print_startup_panel()
        logger.info(f"Maria Helena Bot inicializado para {self.symbol} ({self.timeframe}) no modo {'AO VIVO' if self.live_mode else 'TESTE'}.")

    def _initialize_exchange(self) -> Any:
        """
        Inicializa a instância da exchange CCXT.
        Carrega chaves de API do ambiente ou usa valores padrão.
        """
        exchange_class = getattr(ccxt, self.exchange_name)
        
        exchange_params: Dict[str, Any] = {
            'enableRateLimit': True,
            'options': self.config['OPTIONS'],
            'newUpdates': True,
        }

        if self.config['TESTNET']:
            exchange_params['options']['defaultType'] = 'spot'
            if self.exchange_name == 'binance':
                exchange_params['urls'] = {
                    'api': 'https://testnet.binance.vision/api',
                    'www': 'https://testnet.binance.com'
                }
            logger.info(f"Usando Testnet para {self.exchange_name}.")
        
        api_key = os.getenv(f"{self.exchange_name.upper()}_API_KEY", self.config['API_KEY'])
        secret_key = os.getenv(f"{self.exchange_name.upper()}_SECRET_KEY", self.config['SECRET_KEY'])
        
        if api_key and secret_key and self.live_mode:
            exchange_params['apiKey'] = api_key
            exchange_params['secret'] = secret_key
        elif self.live_mode:
            logger.warning("Modo AO VIVO ativado, mas API_KEY ou SECRET_KEY não configuradas.")
            console.print("[red]ERRO: API_KEY/SECRET_KEY não configuradas para modo AO VIVO![/red]")
            sys.exit(1)
        
        exchange = exchange_class(exchange_params)

        try:
            exchange.load_markets()
            logger.info(f"Conectado à exchange: {self.exchange_name.upper()} (Testnet: {self.config['TESTNET']})")
            if self.live_mode:
                balance = exchange.fetch_balance()
                self.current_balance = balance['total'][self.symbol.split('/')[1]]
                logger.info(f"Saldo atual na exchange: {self.current_balance} {self.symbol.split('/')[1]}")
        except Exception as e:
            console.print(f"[red]❌ Erro ao conectar ou carregar mercados da exchange: {e}[/red]")
            logger.error(f"Erro ao conectar ou carregar mercados da exchange: {e}", exc_info=True)
            sys.exit(1)
            
        return exchange

    def _fetch_ohlcv(self) -> Optional[List[List[float]]]:
        """
        Busca os dados OHLCV (Open, High, Low, Close, Volume) da exchange.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                limit=self.config['LOOKBACK_PERIOD'] + 5
            )
            if not ohlcv:
                console.print(f"[yellow]⚠️ Nenhum dado OHLCV recebido para {self.symbol}.[/yellow]")
                return None
            return ohlcv
        except ccxt.NetworkError as e:
            console.print(f"[red]❌ Erro de rede ao buscar OHLCV: {e}[/red]")
            logger.warning(f"Erro de rede ao buscar OHLCV: {e}")
            return None
        except ccxt.ExchangeError as e:
            console.print(f"[red]❌ Erro da exchange ao buscar OHLCV: {e}[/red]")
            logger.error(f"Erro da exchange ao buscar OHLCV: {e}")
            return None
        except Exception as e:
            console.print(f"[red]❌ Erro inesperado ao buscar OHLCV: {e}[/red]")
            logger.error(f"Erro inesperado ao buscar OHLCV: {e}", exc_info=True)
            return None

    def _get_latest_price(self, ohlcv: List[List[float]]) -> float:
        """Retorna o preço de fechamento da vela mais recente."""
        return ohlcv[-1][4]  # Close price of the last candle

    def _analyze_strategy(self, ohlcv: List[List[float]]) -> Dict[str, Any]:
        """
        Analisa os dados OHLCV usando a estratégia RSI/Volume.
        Retorna um dicionário com o sinal e suas propriedades.
        """
        try:
            # Prepara ticker para o normalizer
            ticker = {
                'last': ohlcv[-1][4],  # Close price
                'quoteVolume': ohlcv[-1][5],  # Volume
                'timestamp': ohlcv[-1][0]  # Timestamp
            }
            
            # Normaliza os dados
            normalized_data = self.normalizer.process(ohlcv, ticker)
            
            # Converte OHLCV para DataFrame para a estratégia
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Analisa com a estratégia
            signal = self.strategy.analyze(df)
            
            # Adiciona preço atual ao sinal
            signal['price'] = self._get_latest_price(ohlcv)
            
            # Adiciona dados normalizados ao sinal
            signal.update(normalized_data)
            
            if self.mentor_mode and self.mentor_processor:
                self.mentor_processor.process_signal(signal)
            
            logger.info(f"SINAL GERADO: {signal}") # <--- CORREÇÃO APLICADA AQUI
            return signal
            
        except Exception as e:
            console.print(f"[red]❌ Erro na análise da estratégia: {e}[/red]")
            logger.error(f"Erro na análise da estratégia: {e}", exc_info=True)
            return {
                'action': 'HOLD', 
                'confidence': 0.0, 
                'price': 0.0,
                'reason': f"Erro na análise: {e}"
            }

    def _process_signal(self, signal: Dict[str, Any]) -> None:
        """Processa sinal de trading"""
        action = signal.get('action', 'HOLD')
        
        if action == 'HOLD':
            return
        
        # 1. Pega preço atual
        current_price = signal.get('price', 0)
        
        if current_price <= 0:
            logger.error("Preço inválido no sinal")
            return
        
        # 2. Calcula tamanho da posição
        position_size_usd = self.risk_manager.calculate_position_size(
            self.current_balance, 
            signal
        )
        
        if position_size_usd <= 0:
            logger.warning("Tamanho de posição calculado é zero ou negativo")
            return
        
        # 3. Valida com CashGate
        can_reserve, reason = self.cash_gate.can_reserve(position_size_usd)
        if not can_reserve:
            console.print(f"[yellow]🚫 CashGate bloqueou: {reason}[/yellow]")
            logger.warning(f"🚫 CashGate bloqueou: {reason}")
            return
        
        # 4. Reserva o capital
        if not self.cash_gate.reserve(position_size_usd):
            logger.error("Falha ao reservar capital no CashGate")
            return
        
        # 5. Executa ordem via OrderManager
        try:
            order = self.order_manager.execute_order(
                action=action,
                amount=position_size_usd / current_price,
                price=current_price,
                signal=signal
            )
            
            if order:
                console.print(f"[green]✅ Ordem executada: {order.get('id', 'N/A')}[/green]")
                logger.info(f"Ordem executada com sucesso: {order}")
            else:
                self.cash_gate.release(position_size_usd)
                console.print("[red]❌ Falha ao executar ordem[/red]")
                logger.error("OrderManager retornou None")
        
        except Exception as e:
            self.cash_gate.release(position_size_usd)
            logger.error(f"Erro ao executar ordem: {e}", exc_info=True)
            console.print(f"[red]❌ Erro: {e}[/red]")

    def _print_startup_panel(self) -> None:
        """Exibe um painel de informações na inicialização do bot."""
        panel_content = Text(justify="center")
        panel_content.append(f"{self.config['BOT_NAME']} v{self.config['BOT_VERSION']}\n", style="bold green")
        panel_content.append(f"Par: [cyan]{self.symbol}[/cyan] | Intervalo: [cyan]{self.timeframe}[/cyan]\n", style="white")
        panel_content.append(f"Exchange: [yellow]{self.exchange_name.upper()}[/yellow] | Testnet: [yellow]{self.config['TESTNET']}[/yellow]\n", style="white")
        panel_content.append(f"Capital Inicial: [green]${self.capital:,.2f}[/green]\n", style="white")
        panel_content.append(f"Modo Mentor: {'[bold magenta]ATIVO[/bold magenta]' if self.mentor_mode else '[dim]DESATIVADO[/dim]'}\n", style="white")
        panel_content.append("\nIniciando operação...\n", style="italic blue")

        console.print(Panel(panel_content, title="🤖 Maria Helena Trading Bot - Status", border_style="bold green"))

    def _print_status_panel(self, current_price: float) -> None:
        """Exibe um painel de status atualizado do bot."""
        panel_content = Text(justify="center")
        panel_content.append(f"Par: [cyan]{self.symbol}[/cyan] | Intervalo: [cyan]{self.timeframe}[/cyan]\n", style="white")
        panel_content.append(f"Preço Atual: [bold green]${current_price:,.2f}[/bold green]\n", style="white")
        
        position_info = self.order_manager.get_position_info()
        if position_info['is_in_position']:
            panel_content.append(
                f"Posição: [yellow]ABERTA[/yellow] | "
                f"Entrada: [yellow]${position_info['entry_price']:,.2f}[/yellow] | "
                f"Quantidade: [yellow]{position_info['amount']:.4f} {self.symbol.split('/')[0]}[/yellow]\n", 
                style="white"
            )
            unrealized_pnl = (current_price - position_info['entry_price']) * position_info['amount']
            pnl_style = "green" if unrealized_pnl >= 0 else "red"
            panel_content.append(f"P&L Não Realizado: [{pnl_style}]${unrealized_pnl:,.2f}[/{pnl_style}]\n", style="white")
        else:
            panel_content.append("[dim]Posição: FECHADA[/dim]\n", style="white")

        circuit_breaker_status = f"{self.circuit_breaker.current_losses}/{self.circuit_breaker.max_losses}"
        if self.circuit_breaker.is_tripped:
            panel_content.append(f"Circuit Breaker: [bold red]ATIVADO[/bold red] ({circuit_breaker_status})\n", style="white")
        else:
            panel_content.append(f"Circuit Breaker: [green]OK[/green] ({circuit_breaker_status})\n", style="white")
        
        console.print(Panel(panel_content, title="⚙️ Status Atual do Bot", border_style="dim"))

    def run(self) -> None:
        """
        Executa o loop principal do bot, buscando dados, analisando e processando sinais.
        """
        while True:
            try:
                ohlcv_data = self._fetch_ohlcv()
                if ohlcv_data:
                    signal = self._analyze_strategy(ohlcv_data)
                    self._process_signal(signal)
                    
                    # Exibe painel de status
                    current_price = self._get_latest_price(ohlcv_data)
                    self._print_status_panel(current_price)
                    
                # Update current balance from exchange for live trading
                if self.live_mode and hasattr(self.exchange, 'fetch_balance'):
                    try:
                        balance = self.exchange.fetch_balance()
                        self.current_balance = balance['total'][self.symbol.split('/')[1]]
                    except Exception as e:
                        logger.warning(f"Erro ao atualizar saldo: {e}")
            
            except ccxt.NetworkError as e:
                console.print(f"[red]❌ Erro de rede: {e}[/red]")
                logger.warning(f"Erro de rede, tentando novamente em {self.check_interval}s. {e}")
            except ccxt.ExchangeError as e:
                console.print(f"[red]❌ Erro da exchange: {e}[/red]")
                logger.error(f"Erro da exchange, tentando novamente em {self.check_interval}s. {e}")
            except Exception as e:
                console.print(f"[red]❌ Erro inesperado no loop principal: {e}[/red]")
                logger.exception("Erro não tratado no loop principal")

            console.print(f"\n[dim]Aguardando {self.check_interval} segundos...[/dim]")
            time.sleep(self.check_interval)


def main() -> None:
    """Função principal de entrada do bot."""
    try:
        bot = MariaHelenaBot()
        bot.run()
    except KeyboardInterrupt:
        console.print("\n[cyan]🛑 Bot interrompido pelo usuário.[/cyan]")
        logger.info("Bot interrompido pelo usuário.")
    except Exception as e:
        console.print(f"[red]❌ Erro fatal: {e}[/red]")
        logger.exception("Erro fatal não tratado no main.")
    finally:
        console.print("\n[bold blue]🚀 Maria Helena Bot encerrado.[/bold blue]")


if __name__ == "__main__":
    main()