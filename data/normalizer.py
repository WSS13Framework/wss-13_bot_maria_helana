"""
📊 Normalizador de Dados - Maria Helena
"Mãe sempre dizia: compare maçãs com maçãs, não com laranjas"

Transforma dados brutos em valores 0-1 para análise consistente
"""

import pandas as pd
import numpy as np
# Importa Console de forma segura, com fallback se rich não estiver instalado
try:
    from rich.console import Console
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

console = Console()
class Normalizer:
    """
    Classe para normalizar dados de mercado financeiro para análise quantitativa.

    Motivação:
    - Indicadores como RSI, volume e preço possuem escalas diferentes.
    - Normalização permite comparar e combinar diferentes features de forma consistente.

    Principais funcionalidades:
    - Normaliza RSI para faixa 0-1.
    - Normaliza volume usando Z-score adaptativo.
    - Normaliza preço usando Min-Max na janela de lookback.
    - Calcula e normaliza momentum (taxa de mudança percentual).
    - Calcula médias móveis e normaliza em relação ao preço atual.
    - Calcula volatilidade dos retornos e normaliza.
    - Identifica tendência geral ('up', 'down', 'neutral') via médias móveis.
    - Garante que todos os valores normalizados estejam entre 0-1 e não sejam NaN.

    Parâmetros:
    - config (dict): Configurações do normalizador, incluindo períodos de lookback e RSI.

    Métodos principais:
    - process(ohlcv, ticker): Processa dados brutos e retorna um dicionário com features normalizadas e brutas.
    - _calculate_rsi(prices, period): Calcula o RSI dos preços.
    - _normalize_volume(current_volume): Normaliza o volume usando Z-score.
    - _normalize_price(current_price, price_series): Normaliza o preço usando Min-Max.
    - _calculate_momentum(prices, period): Calcula o momentum dos preços.
    - _normalize_momentum(momentum): Normaliza o momentum para faixa 0-1.
    - _normalize_volatility(volatility): Normaliza a volatilidade dos retornos.
    - _identify_trend(prices, short, long): Identifica tendência geral do ativo.
    - _safe_value(value): Garante que o valor está entre 0-1 e não é NaN.

    Retorno do método process:
    - dict com features normalizadas e brutas, incluindo RSI, volume, preço, momentum, volatilidade, médias móveis, cruzamento de médias e tendência.

    Normaliza dados de mercado para Maria Helena analisar

    Por que normalizar?
    - RSI vai de 0-100
    - Volume vai de 0 até bilhões
    - Preço vai de 0 até infinito

    Como comparar? NORMALIZANDO tudo para 0-1!
    """

    def __init__(self, config):
        self.lookback = config.get('lookback_period', 100)
        self.rsi_period = config.get('rsi_period', 14)
        
        # Histórico para normalização adaptativa
        self.price_history = []
        self.volume_history = []
        
        console.print("[cyan]📊 Normalizer inicializado[/cyan]")
    
    def process(self, ohlcv, ticker):
        """
        Processa dados brutos e retorna normalizados
        
        Args:
            ohlcv: Lista de candles [[time, o, h, l, c, v], ...]
            ticker: Dict com dados atuais {'last': price, 'volume': vol, ...}
        
        Returns:
            dict: Dados normalizados prontos para estratégia
        """
        
        # Converte para DataFrame
        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        
        # Calcula indicadores técnicos
        rsi = self._calculate_rsi(df['close'], self.rsi_period)
        
        # Normaliza RSI (0-100 → 0-1)
        rsi_norm = rsi / 100.0
        
        # Normaliza Volume (Z-score adaptativo)
        volume_norm = self._normalize_volume(ticker.get('quoteVolume', 0))
        
        # Normaliza Preço (Min-Max na janela)
        price_norm = self._normalize_price(
            ticker['last'], 
            df['close'].tail(self.lookback)
        )
        
        # Calcula momentum (taxa de mudança)
        momentum = self._calculate_momentum(df['close'])
        momentum_norm = self._normalize_momentum(momentum)
        
        # Médias móveis
        ma_fast = df['close'].rolling(window=20).mean().iloc[-1]
        ma_slow = df['close'].rolling(window=50).mean().iloc[-1]
        
        # Normaliza MAs em relação ao preço atual
        ma_fast_norm = ma_fast / ticker['last'] if ticker['last'] > 0 else 1.0
        ma_slow_norm = ma_slow / ticker['last'] if ticker['last'] > 0 else 1.0
        
        # Volatilidade (desvio padrão dos retornos)
        returns = df['close'].pct_change().dropna()
        volatility = returns.std()
        volatility_norm = self._normalize_volatility(volatility)
        
        # Monta resultado
        result = {
            # Indicadores normalizados (0-1)
            'rsi_norm': self._safe_value(rsi_norm),
            'volume_norm': self._safe_value(volume_norm),
            'price_norm': self._safe_value(price_norm),
            'momentum_norm': self._safe_value(momentum_norm),
            'volatility_norm': self._safe_value(volatility_norm),
            
            # Médias móveis (relativas ao preço)
            'ma_fast_norm': self._safe_value(ma_fast_norm),
            'ma_slow_norm': self._safe_value(ma_slow_norm),
            
            # Dados brutos (para referência)
            'price': ticker['last'],
            'volume': ticker.get('quoteVolume', 0),
            'rsi_raw': rsi,
            'timestamp': ticker.get('timestamp', 0),
            
            # Features extras
            'ma_cross': 1 if ma_fast > ma_slow else 0,  # Golden cross
            'trend': self._identify_trend(df['close'])
        }
        
        return result
    
    def _calculate_rsi(self, prices, period=14):
        """
        Calcula RSI (Relative Strength Index)
        
        RSI = 100 - (100 / (1 + RS))
        RS = média dos ganhos / média das perdas
        """
        if len(prices) < period + 1:
            return 50.0  # Neutro se não tem dados suficientes
        
        # Calcula mudanças
        deltas = prices.diff()
        
        # Separa ganhos e perdas
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        # Médias móveis exponenciais
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Evita divisão por zero
        avg_losses = avg_losses.replace(0, 0.0001)
        
        # Calcula RS e RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    
    def _normalize_volume(self, current_volume):
        """
        Normaliza volume usando Z-score
        
        Z-score = (valor - média) / desvio_padrão
        Converte para 0-1: (z + 3) / 6  (assume z entre -3 e +3)
        """
        # Atualiza histórico
        self.volume_history.append(current_volume)
        if len(self.volume_history) > self.lookback:
            self.volume_history = self.volume_history[-self.lookback:]
        
        if len(self.volume_history) < 10:
            return 0.5  # Neutro se poucos dados
        
        mean_vol = np.mean(self.volume_history)
        std_vol = np.std(self.volume_history)
        
        if std_vol == 0:
            return 0.5
        
        z_score = (current_volume - mean_vol) / std_vol
        
        # Converte z-score para 0-1 (clipa em -3 e +3)
        normalized = (np.clip(z_score, -3, 3) + 3) / 6
        
        return normalized
    
    def _normalize_price(self, current_price, price_series):
        """
        Normaliza preço usando Min-Max
        
        norm = (preço - min) / (max - min)
        """
        if len(price_series) < 2:
            return 0.5
        
        min_price = price_series.min()
        max_price = price_series.max()
        
        if max_price == min_price:
            return 0.5
        
        normalized = (current_price - min_price) / (max_price - min_price)
        
        return normalized
    
    def _calculate_momentum(self, prices, period=10):
        """
        Calcula momentum (taxa de mudança percentual)
        """
        if len(prices) < period + 1:
            return 0.0
        
        old_price = prices.iloc[-period]
        current_price = prices.iloc[-1]
        
        if old_price == 0:
            return 0.0
        
        momentum = (current_price - old_price) / old_price
        
        return momentum
    
    def _normalize_momentum(self, momentum):
        """
        Normaliza momentum para 0-1
        
        Assume momentum típico entre -10% e +10%
        """
        # Clipa momentum em -0.10 a +0.10
        clipped = np.clip(momentum, -0.10, 0.10)
        
        # Converte para 0-1
        normalized = (clipped + 0.10) / 0.20
        
        return normalized
    
    def _normalize_volatility(self, volatility):
        """
        Normaliza volatilidade
        
        Volatilidade típica: 0-5% ao dia
        """
        # Clipa em 0-0.05 (5%)
        clipped = np.clip(volatility, 0, 0.05)
        
        # Normaliza para 0-1
        normalized = clipped / 0.05
        
        return normalized
    
    def _identify_trend(self, prices, short=20, long=50):
        """
        Identifica tendência geral
        
        Returns:
            'up', 'down', 'neutral'
        """
        if len(prices) < long:
            return 'neutral'
        
        ma_short = prices.tail(short).mean()
        ma_long = prices.tail(long).mean()
        
        diff_pct = (ma_short - ma_long) / ma_long
        
        if diff_pct > 0.02:  # 2% acima
            return 'up'
        elif diff_pct < -0.02:  # 2% abaixo
            return 'down'
        else:
            return 'neutral'
    
    def _safe_value(self, value):
        """
        Garante que valor está entre 0-1 e não é NaN
        """
        if np.isnan(value) or np.isinf(value):
            return 0.5  # Valor neutro
        
        return np.clip(float(value), 0.0, 1.0)

# Teste rápido
if __name__ == "__main__":
    import sys
    import os
    # Adiciona o diretório pai (raiz do projeto) ao Python path para importação
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from config import CONFIG
    
    console.print("\n[bold cyan]🧪 Testando Normalizer...[/bold cyan]\n")
    
    normalizer = Normalizer(CONFIG)
    
    # Dados fake para teste
    fake_ohlcv = [
        [i, 100+i, 102+i, 98+i, 101+i, 1000000+i*10000]
        for i in range(100)
    ]
    
    fake_ticker = {
        'last': 150,
        'quoteVolume': 1500000,
        'timestamp': 1697472000000
    }
    
    result = normalizer.process(fake_ohlcv, fake_ticker)
    
    console.print("[green]✅ Normalização funcionou![/green]\n")
    console.print("Resultado:")
    for key, value in result.items():
        if isinstance(value, float):
            console.print(f"  {key:20s}: {value:.4f}")
        else:
            console.print(f"  {key:20s}: {value}")
