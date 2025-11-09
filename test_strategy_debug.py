#!/usr/bin/env python3
"""
Testa a estratégia com dados reais para ver onde trava
"""
import ccxt
from config import CONFIG
from data.normalizer import Normalizer
from strategies.rsi_volume_strategy import RSIVolumeStrategy

print("🔍 Iniciando teste de debug...\n")

# 1. Conecta na Binance
print("1. Conectando na Binance...")
exchange = ccxt.binance({'enableRateLimit': True})
print("   ✅ Conectado\n")

# 2. Pega dados
print("2. Pegando dados do BTC/USDT...")
ticker = exchange.fetch_ticker('BTC/USDT')
print(f"   ✅ Preço: ${ticker['last']:,.2f}\n")

print("3. Pegando OHLCV (100 candles de 1h)...")
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
print(f"   ✅ {len(ohlcv)} candles baixados\n")

# 3. Normaliza
print("4. Normalizando dados...")
normalizer = Normalizer(CONFIG)
try:
    normalized = normalizer.process(ohlcv, ticker)
    print(f"   ✅ Normalização OK")
    print(f"      RSI: {normalized['rsi_norm']:.4f} ({normalized['rsi_norm']*100:.1f})")
    print(f"      Vol: {normalized['volume_norm']:.4f}")
    print(f"      Trend: {normalized['trend']}\n")
except Exception as e:
    print(f"   ❌ ERRO na normalização: {e}\n")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. Avalia estratégia
print("5. Avaliando estratégia RSI+Volume...")
strategy = RSIVolumeStrategy(CONFIG)
try:
    signal = strategy.evaluate(normalized)
    if signal:
        print(f"   ✅ SINAL GERADO: {signal['action']}")
    else:
        print(f"   ℹ️  Nenhum sinal (condições não atendidas)")
except Exception as e:
    print(f"   ❌ ERRO na estratégia: {e}\n")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ TESTE COMPLETO! Não deveria travar.")
