#!/usr/bin/env python3
"""
Teste de setup - Verifica se tudo instalou corretamente
Agora com suporte a Testnet/Real baseado no config.py
"""

import ccxt
import pandas as pd
import numpy as np
import talib
from rich.console import Console
from rich.table import Table
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Importa a configuração do bot
from config import CONFIG

console = Console()

print("🧪 Testando instalação...\n")

# --- Teste 1: CCXT (exchanges) ---
print("1️⃣ Testando CCXT (exchanges)...")
try:
    exchange_id = CONFIG['exchange']
    exchange_options = CONFIG.get('options', {})
    
    if CONFIG.get('testnet', False):
        api_key = os.getenv("BINANCE_TESTNET_API_KEY")
        secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY")
        exchange_urls = CONFIG['urls']
        
        exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'urls': exchange_urls,
            **exchange_options,
            'enableRateLimit': True,
        })
        console.print("[yellow]   Conectando à Binance TESTNET...[/yellow]")
    else:
        api_key = os.getenv("BINANCE_API_KEY")
        secret_key = os.getenv("BINANCE_SECRET_KEY")
        
        # Validação para garantir que as chaves não são None
        if not api_key or not secret_key:
            raise ValueError("BINANCE_API_KEY ou BINANCE_SECRET_KEY não encontrados no .env")

        exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            **exchange_options,
            'enableRateLimit': True,
        })
        console.print("[green]   Conectando à Binance REAL...[/green]")

    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"   ✅ CCXT OK - BTC: ${ticker['last']:,.2f}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# --- Teste 2: Pandas ---
print("\n2️⃣ Testando Pandas (dados)...")
try:
    df = pd.DataFrame({'precos': [100, 101, 102]})
    print(f"   ✅ Pandas OK - Média: {df['precos'].mean()}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# --- Teste 3: TA-Lib ---
print("\n3️⃣ Testando TA-Lib (indicadores)...")
try:
    # CORREÇÃO APLICADA AQUI: dtype=np.double
    prices = np.array([100, 101, 102, 103, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104], dtype=np.double)
    rsi = talib.RSI(prices, timeperiod=14)
    print(f"   ✅ TA-Lib OK - RSI: {rsi[-1]:.2f}")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# --- Teste 4: Rich ---
print("\n4️⃣ Testando Rich (visualização)...")
try:
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

print("\n🎉 Setup completo! Pronto para começar!\n")