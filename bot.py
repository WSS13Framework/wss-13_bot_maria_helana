#!/usr/bin/env python3
"""
🤖 MARIA HELENA Trading Bot v0.2
Agora com modo de aprendizado e variáveis de ambiente!
"""
import ccxt # type: ignore
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import requests # Para enviar mensagens para o Telegram
import logging # Importar logging

# --- Adicione estas duas linhas para carregar o .env ---
from dotenv import load_dotenv
import os
load_dotenv() # Carrega as variáveis do arquivo .env
# ------------------------------------------------------

from config import CONFIG
from protection.risk_manager import RiskManager # type: ignore
from protection.technical_guard import TechnicalGuard # type: ignore
from protection.circuit_breaker import CircuitBreaker # type: ignore
from strategies.mentor_signal_processor import MentorSignalProcessor
from data.normalizer import Normalizer

# --- NOVAS IMPORTAÇÕES ---
from protection.cash_gate.cash_gate import CashGate # Importa o CashGate
from core.orders.order_manager import OrderManager # Importa o OrderManager
# --- FIM NOVAS IMPORTAÇÕES ---

# Configuração básica de logging para o bot principal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Logger específico para o bot.py

console = Console()

class MariaHelena:
    """
    Maria Helena - Trading Bot

    Uma homenagem à minha mãe, que me ensinou disciplina,
    paciência e a importância de fazer as coisas com amor.

    Principais características:
    - Carrega variáveis de ambiente essenciais para integração com Telegram, Binance e dashboard.
    - Valida configuração das variáveis e interrompe execução se faltar algo crítico.
    - Conecta à Binance via CCXT para trading spot.
    - Implementa múltiplas camadas de proteção: Normalizer, RiskManager, TechnicalGuard e CircuitBreaker.
    - Suporta modo mentoria para aprendizado e processamento de sinais.
    - Envia notificações formatadas e atualizações de status para o Telegram.
    - Exibe mensagens de inicialização e desligamento estilizadas usando Rich.
    - Busca e exibe dados de mercado (ticker, OHLCV) com tratamento de erros e ativação do circuit breaker.
    - Loop principal roda continuamente, checando saúde do bot e respondendo a emergências.
    - Proporciona desligamento seguro, salvando estado e reportando estatísticas de aprendizado.

    Métodos:
    - __init__: Inicializa o bot, carrega configuração, prepara exchange e proteções, envia mensagem de início.
    - send_telegram_message: Envia mensagens formatadas para o Telegram configurado.
    - show_birth_message: Mostra mensagem estilizada de início com detalhes e qualidades do bot.
    - get_market_data: Busca dados atuais do mercado e trata erros de API.
    - run: Loop principal, busca dados, checa saúde e reporta status periodicamente.
    - check_health: Avalia saúde geral, ativa circuit breaker se necessário e envia alertas.
    - show_goodbye_message: Mostra mensagem de resumo ao desligar, incluindo tempo de execução e estatísticas.
    - shutdown: Desliga o bot de forma segura, salva estado e reporta estatísticas de aprendizado.

    Atributos:
    - name: Nome do bot.
    - version: Versão do bot.
    - birth_date: Data de inicialização.
    - telegram_bot_token, telegram_chat_id: Credenciais de integração com Telegram.
    - binance_api_key, binance_secret_key: Credenciais de API da Binance.
    - dashboard_username, dashboard_password: Credenciais do dashboard.
    - exchange: Instância CCXT da Binance.
    - symbol: Símbolo de trading.
    - capital: Capital inicial de trading.
    - normalizer, risk_manager, tech_guard, circuit_breaker: Camadas de proteção.
    - mentor_mode: Flag para modo mentoria.
    - mentor_processor: Instância do processador de sinais de mentoria (se ativado).
    """

    def __init__(self):
        """
        Pense diferente. Maria Helena foi criada com clareza, disciplina e amor—como Steve Jobs exigiria.
        - Carrega variáveis de ambiente de forma transparente, garantindo integração com Telegram, Binance e dashboard.
        - Valida cada variável crítica; se faltar algo essencial, o bot interrompe—sem concessões.
        - Conecta à Binance usando ccxt, prezando pela simplicidade e confiabilidade.
        - Inicializa parâmetros de trading (símbolo, capital) a partir do CONFIG, mantendo a configuração elegante e centralizada.
        - Instancia camadas de proteção: Normalizer, RiskManager, TechnicalGuard, CircuitBreaker—cada uma um pilar de segurança.
        - O modo mentoria é opcional, mas quando ativado, potencializa aprendizado e processamento de sinais.
        - Define o capital inicial no CircuitBreaker, garantindo que o bot conheça seus limites.
        - Exibe uma mensagem de nascimento e envia notificação ao Telegram, celebrando cada início bem-sucedido.
        Erros não são tolerados: se algo falhar, o bot encerra de forma elegante, informando o problema.
        """
        self.name = "Maria Helena"
        self.version = "0.2.0 - Mentor Mode"
        self.birth_date = datetime.now().strftime("%d/%m/%Y")
        
        # --- Carrega variáveis de ambiente ---
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        self.binance_secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.dashboard_username = os.getenv("DASHBOARD_USERNAME")
        self.dashboard_password = os.getenv("DASHBOARD_PASSWORD")
        # -------------------------------------

        # Validação básica das variáveis de ambiente
        if not all([self.telegram_bot_token, self.telegram_chat_id, 
                    self.binance_api_key, self.binance_secret_key]):
            console.print("[red]❌ ERRO: Variáveis de ambiente essenciais (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_SECRET_KEY) não configuradas no .env![/red]")
            exit(1) # Sai do programa se as variáveis não estiverem configuradas
        
        # Exchange
        exchange_config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
            'apiKey': self.binance_api_key,       # Usa a chave API do .env
            'secret': self.binance_secret_key,    # Usa a chave SECRETA do .env
        }

        # --- CONFIGURAÇÃO PARA TESTNET/SANDBOX ---
        # A variável de ambiente USE_SANDBOX ou o CONFIG['testnet'] controlam isso
        use_sandbox_env = os.getenv("USE_SANDBOX", "0").lower() == "1"
        if CONFIG.get('testnet', False) or use_sandbox_env:
            console.print("[yellow]⚠️  Modo TESTNET/SANDBOX ATIVADO![/yellow]")
            exchange_config['options']['defaultType'] = 'future' # Testnet spot da Binance é mais limitada, usar future para testar ordens
            exchange_config['urls'] = {
                'api': 'https://testnet.binancefuture.com/fapi/v1', # URL da testnet de futuros da Binance
                'private': 'https://testnet.binancefuture.com/fapi/v1',
                'public': 'https://testnet.binancefuture.com/fapi/v1'
            }
            # Para testnet spot, a URL seria 'https://testnet.binance.vision/api'
            # Mas a testnet spot da Binance tem limitações e pode não funcionar bem para ordens de mercado.
            # A testnet de futuros é mais robusta para testes.
            self.symbol = 'BTC/USDT:USDT' # Símbolo para futuros
        else:
            console.print("[green]✅ Modo LIVE/PRODUÇÃO ATIVADO![/green]")
        # --- FIM CONFIGURAÇÃO TESTNET/SANDBOX ---

        self.exchange = ccxt.binance(exchange_config)
        
        # --- Bloco de inicialização de parâmetros principais ---
        # 1. Símbolo de trading e capital inicial
        self.symbol = CONFIG['symbol'] if not (CONFIG.get('testnet', False) or use_sandbox_env) else self.symbol # Mantém o símbolo de futuros se testnet
        self.capital = CONFIG['initial_capital']
        # Possíveis erros: símbolo inválido, capital não numérico ou negativo

        # 2. Proteções (3 camadas)
        self.normalizer = Normalizer(CONFIG)  # Normaliza dados de entrada
        self.risk_manager = RiskManager(CONFIG)  # Gerencia risco e limites de operação
        self.tech_guard = TechnicalGuard()  # Protege contra erros técnicos e API
        self.circuit_breaker = CircuitBreaker(CONFIG)  # Interrompe operações em emergências
        
        # --- INSTANCIAÇÃO DO CASHGATE (NOVO) ---
        self.cash_gate = CashGate(initial_capital=self.capital)
        # --- FIM INSTANCIAÇÃO DO CASHGATE ---

        # --- INSTANCIAÇÃO DO ORDERMANAGER (NOVO) ---
        # O OrderManager precisa de todas as dependências de proteção
        self.order_manager = OrderManager(
            exchange=self.exchange,
            risk_manager=self.risk_manager,
            technical_guard=self.tech_guard,
            circuit_breaker=self.circuit_breaker,
            cash_gate=self.cash_gate # Passa a instância do CashGate
        )
        # --- FIM INSTANCIAÇÃO DO ORDERMANAGER ---

        # 3. Modo mentoria (NOVO!)
        self.mentor_mode = CONFIG.get('mentor_mode', False)
        if self.mentor_mode:
            self.mentor_processor = MentorSignalProcessor(
            self.normalizer,
            self.risk_manager
            )
        # Possíveis erros: mentor_mode ativado sem dependências corretas

        # 4. Inicializa Circuit Breaker com capital
        # O capital inicial para o Circuit Breaker deve vir do CashGate para consistência
        self.circuit_breaker.set_initial_capital(self.cash_gate.current_capital)
        # Possíveis erros: capital não informado ou inválido

        # 5. Mensagem de inicialização
        self.show_birth_message()
        self.send_telegram_message(f"🤖 Maria Helena v{self.version} iniciada com sucesso! Capital: ${self.cash_gate.current_capital:,.2f}")
        # Possíveis erros: falha na conexão Telegram, variáveis de ambiente faltando
    
    def send_telegram_message(self, message):
        """Envia uma mensagem para o Telegram."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            console.print("[yellow]⚠️  Token ou Chat ID do Telegram não configurados. Não foi possível enviar a mensagem.[/yellow]")
            return

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML" # Permite formatação como negrito, itálico, etc.
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status() # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
            # console.print(f"[green]✅ Mensagem Telegram enviada.[/green]")
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Erro ao enviar mensagem Telegram: {e}[/red]")

    def show_birth_message(self):
        """Mensagem de inicialização"""
        title = Text()
        title.append("🤖 ", style="bold cyan")
        title.append(self.name.upper(), style="bold magenta")
        title.append(" Trading Bot", style="bold cyan")
        
        message = Text()
        message.append("❤️  Nomeada em homenagem à minha mãe\n", style="italic red")
        message.append(f"📅 Nascimento: {self.birth_date}\n", style="cyan")
        message.append(f"🔢 Versão: {self.version}\n", style="cyan")
        message.append(f"💰 Capital Inicial: ${self.cash_gate.current_capital:,.2f}\n", style="green bold") # Usa capital do CashGate
        message.append(f"📊 Símbolo: {self.symbol}\n", style="yellow")
        message.append("\n")
        message.append("💪 Qualidades:\n", style="bold white")
        message.append("   • Disciplinada\n", style="white")
        message.append("   • Paciente\n", style="white")
        message.append("   • Protetora\n", style="white")
        message.append("   • Consistente\n", style="white")
        message.append("   💰 Cash Gate: Guardião do Capital\n", style="magenta") # Adiciona Cash Gate
        
        console.print(Panel(
            message,
            title=title,
            border_style="magenta",
            padding=(1, 2)
        ))
    
    def get_market_data(self):
        """Coleta dados do mercado"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol, 
                CONFIG['timeframe'], 
                limit=CONFIG['lookback_period']
            )
            self.tech_guard.reset_error_counter() # Reseta contador de erros se a chamada foi bem-sucedida
            return ticker, ohlcv
        except Exception as e:
            action = self.tech_guard.handle_error(e, context="Erro ao pegar dados do mercado")
            self.send_telegram_message(f"🚨 <b>Maria Helena:</b> Erro ao pegar dados do mercado: {str(e)[:100]}... Ação: {action}")
            if action == 'stop':
                self.circuit_breaker.activate_kill_switch("TECHNICAL_FAILURE", f"Muitos erros de API: {e}")
            return None, None
    
    def run(self):
        """Loop principal - Maria Helena nunca para!"""
        console.print(
            f"\n[yellow]⏰ {self.name} está trabalhando... "
            f"(Ctrl+C para pausar)[/yellow]\n"
        )
        
        iteration = 0
        start_time = datetime.now()
        
        try:
            while True:
                iteration += 1
                now = datetime.now().strftime("%H:%M:%S")
                
                # Verifica a saúde do bot antes de cada iteração
                self.check_health()
                if self.circuit_breaker.kill_switch_active:
                    console.print("\n[red bold]⚡ KILL SWITCH ATIVO - ENCERRANDO[/red bold]")
                    self.send_telegram_message("🚨 <b>Maria Helena:</b> KILL SWITCH ATIVO! Encerrando operações.")
                    self.shutdown()
                    exit(1)

                # Pega dados do mercado
                ticker, ohlcv = self.get_market_data()
                
                if ticker:
                    price = ticker['last']
                    volume = ticker['quoteVolume']
                    change_24h = ticker.get('percentage', 0)
                    
                    # Status visual
                    emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                    color = "green" if change_24h > 0 else "red" if change_24h < 0 else "yellow"
                    
                    status_message = (
                        f"[cyan]{now}[/cyan] {emoji} "
                        f"{self.symbol}: [bold]${price:,.2f}[/bold] "
                        f"[{color}]({change_24h:+.2f}%)[/{color}] | "
                        f"Vol: ${volume:,.0f} | "
                        f"#{iteration}"
                    )
                    console.print(status_message)
                    # self.send_telegram_message(status_message) # Opcional: enviar cada atualização para o Telegram (pode ser muito spam)
                else:
                    console.print(f"[red]{now} | ❌ Não foi possível obter dados do mercado. Pulando iteração.[/red]")
                
                # --- MENTOR MODE: Pergunta se tem sinal e executa trade ---
                if self.mentor_mode and iteration % 5 == 0:  # A cada 5 iterações
                    mentor_signal = self.receive_mentor_signal_manual()
                    
                    if mentor_signal:
                        decision = self.mentor_processor.receive_mentor_signal(mentor_signal)
                        
                        if decision['should_execute']:
                            logger.info(f"Maria Helena decidiu executar trade. Sinal: {decision['final_signal']}")
                            trade_result = self.order_manager.execute_trade(decision['final_signal'])
                            
                            if trade_result.get("status") == "executed":
                                console.print(f"[green]✅ Trade executado com sucesso! Ordem ID: {trade_result['order'].get('id')}[/green]")
                                self.send_telegram_message(f"✅ <b>Maria Helena:</b> Trade executado! {decision['final_signal'].get('action')} {decision['final_signal'].get('symbol')} @ {decision['final_signal'].get('price'):.2f}")
                                # O CashGate e RiskManager são atualizados internamente pelo OrderManager
                            else:
                                console.print(f"[red]❌ Falha ao executar trade: {trade_result.get('reason')}[/red]")
                                self.send_telegram_message(f"❌ <b>Maria Helena:</b> Falha ao executar trade: {trade_result.get('reason')}")
                # --- FIM MENTOR MODE ---

                # Maria Helena é paciente, espera 1 minuto
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.show_goodbye_message(start_time, iteration)
            self.send_telegram_message("👋 <b>Maria Helena:</b> Bot finalizado pelo usuário.")
        except Exception as e:
            console.print(f"[red]❌ ERRO CRÍTICO NO LOOP PRINCIPAL: {e}[/red]")
            self.send_telegram_message(f"🚨 <b>Maria Helena:</b> ERRO CRÍTICO NO LOOP PRINCIPAL: {str(e)[:200]}... Encerrando operações.")
            self.circuit_breaker.activate_kill_switch("CRITICAL_ERROR", f"Loop principal: {e}")
            self.shutdown()
            exit(1)
    
    def check_health(self):
        """Verifica saúde geral do bot e ativa o Circuit Breaker se necessário."""
        risk_status = self.risk_manager.get_status()
        tech_status_action, _ = self.tech_guard.should_emergency_stop() # Retorna 'stop' ou 'ok'
        
        is_healthy, problems = self.circuit_breaker.check_health(
            self.cash_gate.current_capital, # O capital atual do bot vem do CashGate
            risk_status,
            tech_status_action # Passa a ação recomendada pelo tech_guard
        )
        
        if not is_healthy:
            console.print("[red]🚨 PROBLEMAS DETECTADOS:[/red]")
            for problem in problems:
                console.print(f"   {problem}")
                self.send_telegram_message(f"⚠️ <b>Maria Helena:</b> Problema detectado: {problem}")
            
            if self.circuit_breaker.kill_switch_active:
                console.print("\n[red bold]⚡ KILL SWITCH ATIVO - ENCERRANDO[/red bold]")
                self.send_telegram_message("🚨 <b>Maria Helena:</b> KILL SWITCH ATIVO! Encerrando operações.")
                self.shutdown()
                exit(1) # Encerra o programa imediatamente
    
    def show_goodbye_message(self, start_time, iterations):
        """Mensagem de despedida"""
        duration = datetime.now() - start_time
        hours = duration.total_seconds() / 3600
        
        message = Text()
        message.append(f"👋 {self.name} vai descansar agora\n\n", style="bold yellow")
        message.append(f"⏱️  Tempo trabalhado: {hours:.2f} horas\n", style="cyan")
        message.append(f"🔄 Iterações: {iterations}\n", style="cyan")
        message.append(f"💰 Capital: ${self.cash_gate.current_capital:,.2f}\n", style="green") # Usa capital do CashGate
        message.append("\n")
        message.append("❤️  Obrigado, mãe, por me inspirar!", style="italic red")
        
        console.print(Panel(
            message,
            title="[magenta]Maria Helena - Sessão Finalizada[/magenta]",
            border_style="magenta"
        ))
    
    def shutdown(self):
        """Desligamento seguro"""
        console.print("\n[yellow]👋 Maria Helena encerrando...[/yellow]")
        
        # Salva estado
        self.circuit_breaker.save_state({
            'capital': self.cash_gate.current_capital, # Usa capital do CashGate
            'total_trades': self.risk_manager.total_trades,
            'daily_pnl': self.risk_manager.daily_pnl
        })
        
        # Stats de aprendizado
        if self.mentor_mode:
            self.mentor_processor.get_learning_stats()
        
        console.print("[green]✅ Estado salvo. Até logo! ❤️[/green]")

if __name__ == "__main__":
    maria = MariaHelena()
    maria.run()