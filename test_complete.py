#!/usr/bin/env python3
import ccxt
import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import os

console = Console()

def test_wss13_system():
    """Teste completo do sistema WSS+13"""
    
    console.print(Panel("🎯 WSS+13 - Teste Completo", style="bold blue"))
    
    # 1. Testar conexão API
    try:
        config_path = os.path.expanduser('~/.binance_config')
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
        
        exchange = ccxt.binance({
            'apiKey': config['BINANCE_API_KEY'],
            'secret': config['BINANCE_SECRET_KEY'],
            'sandbox': config.get('BINANCE_TESTNET', 'false').lower() == 'true',
            'enableRateLimit': True,
        })
        
        # Testar acesso
        balance = exchange.fetch_balance()
        console.print("✅ Conexão API: OK", style="green")
        
        # Mostrar informações da conta
        table = Table(title="📊 Informações da Conta")
        table.add_column("Asset", style="cyan")
        table.add_column("Free", style="green")
        table.add_column("Used", style="yellow")
        table.add_column("Total", style="blue")
        
        for asset, info in balance.items():
            if isinstance(info, dict) and info.get('total', 0) > 0:
                table.add_row(
                    asset,
                    f"{info.get('free', 0):.8f}",
                    f"{info.get('used', 0):.8f}",
                    f"{info.get('total', 0):.8f}"
                )
        
        console.print(table)
        
        # 2. Testar dados de mercado
        ticker = exchange.fetch_ticker('BTC/USDT')
        console.print(f"\n📈 BTC/USDT: ${ticker['last']:,.2f}", style="bold green")
        
        # 3. Testar análise técnica
        console.print("\n🔍 Teste de Análise Técnica:", style="yellow")
        
        # Buscar dados históricos
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=20)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calcular média móvel simples
        df['sma_10'] = df['close'].rolling(10).mean()
        
        console.print(f"📊 Preço atual: ${df['close'].iloc[-1]:,.2f}")
        console.print(f"📈 SMA(10): ${df['sma_10'].iloc[-1]:,.2f}")
        
        if df['close'].iloc[-1] > df['sma_10'].iloc[-1]:
            console.print("🟢 Tendência: ALTA", style="green")
        else:
            console.print("🔴 Tendência: BAIXA", style="red")
        
        console.print("\n🎉 Sistema WSS+13 funcionando perfeitamente!", style="bold green")
        return True
        
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="red")
        return False

if __name__ == "__main__":
    test_wss13_system()
