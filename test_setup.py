#!/usr/bin/env python3
"""
Teste de setup - Verifica se tudo instalou corretamente
"""

print("�� Testando instalação...\n")

# Teste 1: CCXT
print("1️⃣ Testando CCXT (exchanges)...")
try:
    import ccxt
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"   ✅ CCXT OK - BTC: ${ticker['last']:,.2f}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# Teste 2: Pandas
print("\n2️⃣ Testando Pandas (dados)...")
try:
    import pandas as pd
    df = pd.DataFrame({'precos': [100, 101, 102]})
    print(f"   ✅ Pandas OK - Média: {df['precos'].mean()}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# Teste 3: TA-Lib
print("\n3️⃣ Testando TA-Lib (indicadores)...")
try:
    import talib
    import numpy as np # <-- Adicione ou verifique esta linha
    # Altere esta linha para incluir dtype=np.float64
    prices = np.array([100, 101, 102, 103, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104], dtype=np.float64)
    rsi = talib.RSI(prices, timeperiod=14)
    print(f"   ✅ TA-Lib OK - RSI: {rsi[-1]:.2f}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# Teste 4: Rich (terminal bonito)
print("\n4️⃣ Testando Rich (visualização)...")
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title="Setup Completo!")
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("Python", "✅")
    table.add_row("CCXT", "✅")
    table.add_row("Pandas", "✅")
    table.add_row("TA-Lib", "✅")
    console.print(table)
    print("   ✅ Rich OK")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

