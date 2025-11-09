#!/usr/bin/env python3
# ARQUIVO: maria_helena_analista.py
# FUNÇÃO NO ECOSSISTEMA MARIA HELENA:
# Este é o "Analista". Sua única função é coletar, processar e
# armazenar dados de mercado enriquecidos. Ele busca dados brutos (velas)
# de múltiplos ativos, calcula um conjunto de indicadores técnicos
# (RSI, MACD, BB, etc.) e salva essa análise estruturada no banco de
# dados v2.0. Ele é o provedor de inteligência para o ecossistema.

"""
MARIA HELENA v4.0 - DATA ANALYST BOT
"""

import sqlite3
from datetime import datetime
import logging
import time
import sys
import requests
from pathlib import Path

# CORREÇÃO: Imports que faltavam
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/maria_helena_analista.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MariaHelena.Analista')


class MariaHelenaAnalystBot:
    """Bot de análise de mercado que calcula 5 indicadores e salva no DB."""
    
    def __init__(self):
        self.db_path = Path.home() / 'maria-helena' / 'data' / 'maria_helena_signals.db'
        self.binance_url = "https://api.binance.com/api/v3"
        self.assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT']
        self.init_database()
    
    def init_database(self):
        """Garante que o banco de dados e a tabela principal existem."""
        logger.info(f"🔧 Verificando banco de dados em: {self.db_path}...")
        if not self.db_path.exists():
            logger.error("❌ Banco de dados não encontrado!")
            logger.error("   Execute 'maria_helena_database_creator.py' primeiro.")
            sys.exit(1)
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_analysis_v2'")
            if not cursor.fetchone():
                logger.error("❌ Tabela 'market_analysis_v2' não encontrada no banco de dados!")
                sys.exit(1)
            conn.close()
            logger.info("✅ Banco de dados e tabela verificados com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao verificar o banco de dados: {e}")
            sys.exit(1)

    def fetch_klines(self, symbol, interval='1m', limit=100):
        """Busca velas (klines) da API da Binance."""
        try:
            url = f"{self.binance_url}/klines"
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erro ao buscar klines para {symbol}: {e}")
            return []

    def calculate_rsi(self, prices, period=14):
        if len(prices) < period: return 50.0
        prices_series = pd.Series(prices)
        delta = prices_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return round(100 - (100 / (1 + rs.iloc[-1])), 2)

    def calculate_bollinger_bands(self, prices, period=20, num_std=2):
        if len(prices) < period: return None, None, None
        prices_series = pd.Series(prices)
        rolling_mean = prices_series.rolling(window=period).mean()
        rolling_std = prices_series.rolling(window=period).std()
        upper_band = rolling_mean.iloc[-1] + (rolling_std.iloc[-1] * num_std)
        return round(upper_band, 2), round(rolling_mean.iloc[-1], 2), round(rolling_mean.iloc[-1] - (rolling_std.iloc[-1] * num_std), 2)

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        if len(prices) < slow: return None, None, None
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
        ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return round(macd_line.iloc[-1], 4), round(signal_line.iloc[-1], 4), round((macd_line - signal_line).iloc[-1], 4)

    def calculate_sma(self, prices, period=50):
        if len(prices) < period: return None
        return round(np.mean(prices[-period:]), 2)

    def calculate_obv(self, prices, volumes):
        if len(prices) < 2: return 0.0
        obv = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]: obv += volumes[i]
            elif prices[i] < prices[i-1]: obv -= volumes[i]
        return round(obv, 2)

    def determine_trend(self, prices, short_period=12, long_period=50):
        if len(prices) < long_period: return "NEUTRAL"
        sma_short = np.mean(prices[-short_period:])
        sma_long = np.mean(prices[-long_period:])
        if sma_short > sma_long: return "BULLISH"
        elif sma_short < sma_long: return "BEARISH"
        else: return "NEUTRAL"

    def save_analysis(self, analysis_data):
        """Salva um lote de análises no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO market_analysis_v2 
                (asset, timestamp, price, volume, rsi, bb_upper, bb_lower, bb_middle, 
                 macd, macd_signal, macd_histogram, sma, obv, trend)
                VALUES (:asset, :timestamp, :price, :volume, :rsi, :bb_upper, :bb_lower, :bb_middle, 
                 :macd, :macd_signal, :macd_histogram, :sma, :obv, :trend)
            """, analysis_data)
            conn.commit()
            logger.info(f"💾 {cursor.rowcount} novos registros salvos no banco de dados.")
        except sqlite3.Error as e:
            logger.error(f"❌ ERRO ao salvar lote no banco de dados: {e}")
        finally:
            if conn: conn.close()

    def analyze_asset(self, symbol):
        """Análise completa de um único ativo."""
        klines = self.fetch_klines(symbol, interval='1m', limit=100)
        if not klines or len(klines) < 50:
            logger.warning(f"⚠️ Dados insuficientes para análise de {symbol}")
            return None
        
        prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        timestamp = int(klines[-1][0] / 1000)

        rsi = self.calculate_rsi(prices)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
        macd, macd_signal, macd_histogram = self.calculate_macd(prices)
        sma = self.calculate_sma(prices)
        obv = self.calculate_obv(prices, volumes)
        trend = self.determine_trend(prices)
        

        return {
            'asset': symbol, 'timestamp': timestamp, 'price': prices[-1], 'volume': volumes[-1],
            'rsi': rsi, 'bb_upper': bb_upper, 'bb_lower': bb_lower, 'bb_middle': bb_middle,
            'macd': macd, 'macd_signal': macd_signal, 'macd_histogram': macd_histogram,
            'sma': sma, 'obv': obv, 'trend': trend
        }

    def run(self):
        """Executa o bot continuamente."""
        logger.info("\n" + "="*60)
        logger.info("🚀 MARIA HELENA v4.0 - ANALYST BOT - INICIANDO")
        logger.info("="*60)
        
        cycle = 0
        while True:
            cycle += 1
            logger.info(f"\n🔄 CICLO DE ANÁLISE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            all_analyses = []
            for asset in self.assets:
                analysis = self.analyze_asset(asset)
                if analysis:
                    all_analyses.append(analysis)
                time.sleep(1) # Rate limit para a API
            
            if all_analyses:
                self.save_analysis(all_analyses)
            
            logger.info(f"✅ Ciclo #{cycle} concluído. Próximo em 60 segundos...")
            time.sleep(60)

if __name__ == "__main__":
    try:
        # CORREÇÃO: Criar diretório de logs se não existir
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        bot = MariaHelenaAnalystBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erro fatal não tratado: {e}", exc_info=True)
        sys.exit(1)
