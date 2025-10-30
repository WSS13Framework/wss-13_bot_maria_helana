# protection/technical_guard.py

import ccxt
from datetime import datetime
from rich.console import Console
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

console = Console()

class TechnicalGuard:
    """
    Guarda Técnico - SEGUNDA CAMADA DE PROTEÇÃO
    
    Protege contra:
    1. Erros de API
    2. Problemas de rede
    3. Dados inválidos
    4. Exchange offline
    """
    
    def __init__(self):
        self.error_count = 0
        self.max_errors = 5
        self.last_error_time = None
        self.exchange_status = 'unknown'
        
        logger.info("[yellow]🔧 Camada 2: Technical Guard ativado[/yellow]")
    
    def validate_api_connection(self, exchange):
        """
        Valida conexão com exchange
        
        Returns:
            (bool, str): (conectado, mensagem)
        """
        try:
            # Tenta pegar status da exchange
            # Usamos fetch_status para Binance, que é mais leve que load_markets
            status = exchange.fetch_status()
            if status and status.get('status') == 'ok':
                self.exchange_status = 'online'
                self.reset_error_counter()
                return True, "✅ Exchange online"
            else:
                self.error_count += 1
                self.last_error_time = datetime.now()
                return False, f"⚠️  Exchange retornou status: {status.get('status', 'desconhecido')}"
        
        except ccxt.NetworkError as e:
            self.error_count += 1
            self.last_error_time = datetime.now()
            return False, f"�� Erro de rede: {str(e)[:50]}"
        
        except ccxt.ExchangeError as e:
            self.error_count += 1
            return False, f"⚠️  Erro da exchange: {str(e)[:50]}"
        
        except Exception as e:
            self.error_count += 1
            return False, f"❌ Erro desconhecido: {str(e)[:50]}"
    
    def validate_ticker_data(self, ticker):
        """
        Valida dados de ticker
        
        Returns:
            (bool, str, dict): (válido, razão, dados_limpos)
        """
        if not ticker:
            return False, "Ticker vazio", None
        
        required_fields = ['last', 'bid', 'ask', 'high', 'low', 'volume']
        
        # Verifica campos obrigatórios
        for field in required_fields:
            if field not in ticker:
                return False, f"Campo '{field}' faltando", None
            
            if ticker[field] is None:
                return False, f"Campo '{field}' é None", None
            
            # Alguns campos podem ser 0 (ex: volume em mercados de baixa liquidez)
            # Mas last, bid, ask, high, low não devem ser <= 0
            if field in ['last', 'bid', 'ask', 'high', 'low'] and ticker[field] <= 0:
                return False, f"Campo '{field}' inválido: {ticker[field]}", None
        
        # Valida lógica (bid < last < ask)
        if not (ticker['bid'] <= ticker['last'] <= ticker['ask']):
            return False, f"Preços ilógicos: bid={ticker['bid']} last={ticker['last']} ask={ticker['ask']}", None
        
        # Dados limpos e validados
        clean_data = {
            'price': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'volume_24h': ticker['volume'],
            'timestamp': ticker.get('timestamp', datetime.now().timestamp() * 1000)
        }
        
        return True, "✅ Ticker válido", clean_data
    
    def validate_ohlcv_data(self, ohlcv, min_candles=50):
        """
        Valida dados OHLCV
        
        Returns:
            (bool, str): (válido, razão)
        """
        if not ohlcv:
            return False, "OHLCV vazio"
        
        if len(ohlcv) < min_candles:
            return False, f"Poucos candles: {len(ohlcv)} < {min_candles}"
        
        # Valida estrutura de cada candle
        for i, candle in enumerate(ohlcv[-10:]):  # Valida últimos 10
            if len(candle) != 6:
                return False, f"Candle {i} com estrutura errada (esperado 6 elementos)"
            
            timestamp, open_, high, low, close, volume = candle
            
            # Valida lógica OHLC
            if not (low <= open_ <= high and low <= close <= high):
                return False, f"Candle {i} com OHLC ilógico: O={open_}, H={high}, L={low}, C={close}"
            
            if high <= 0 or low <= 0:
                return False, f"Candle {i} com preços inválidos (<= 0)"
            
            if volume < 0:
                return False, f"Candle {i} com volume negativo"
        
        return True, "✅ OHLCV válido"
    
    def should_emergency_stop(self):
        """
        Verifica se deve parar emergencialmente
        
        Returns:
            (bool, str): (parar, razão)
        """
        # Muitos erros consecutivos
        if self.error_count >= self.max_errors:
            return 'stop', f"🚨 EMERGENCY STOP: {self.error_count} erros consecutivos"
        
        # Exchange offline há muito tempo
        if self.exchange_status == 'offline':
            return 'stop', "🚨 EMERGENCY STOP: Exchange offline"
        
        return 'ok', "OK"
    
    def reset_error_counter(self):
        """Reseta contador de erros (após sucesso)"""
        if self.error_count > 0:
            logger.info(f"[green]↻ Reset: erros {self.error_count} → 0[/green]")
            self.error_count = 0
    
    def handle_error(self, error, context=""):
        """
        Manipula erro de forma segura
        
        Returns:
            str: Ação recomendada ('retry', 'skip', 'stop')
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        logger.error(f"[red]❌ Erro #{self.error_count}: {context}[/red]")
        logger.error(f"[red]   {str(error)[:100]}[/red]")
        
        # Decide ação
        if self.error_count < 3:
            return 'retry'  # Tenta novamente
        elif self.error_count < self.max_errors:
            return 'skip'   # Pula esta iteração
        else:
            return 'stop'   # Para o bot
