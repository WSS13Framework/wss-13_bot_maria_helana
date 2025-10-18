#!/usr/bin/env python3
"""
Trading Bot - Versão 0.1
Pop!_OS Edition
"""

import ccxt
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from config import CONFIG

console = Console()

class TradingBot:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = CONFIG['symbol']
        self.capital = CONFIG['initial_capital']
        
        console.print(Panel.fit(
            f"[bold green]🤖 Trading Bot Iniciado[/bold green]\n"
            f"Symbol: {self.symbol}\n"
            f"Capital: ${self.capital:,.2f}",
            title="Bot v0.1"
        ))
    
    def get_market_data(self):
        """Pega dados atuais do mercado"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol, 
                CONFIG['timeframe'], 
                limit=100
            )
            return ticker, ohlcv
        except Exception as e:
            console.print(f"[red]❌ Erro ao pegar dados: {e}[/red]")
            return None, None
    
    def run(self):
        """Loop principal"""
        console.print("[yellow]⏰ Bot rodando... (Ctrl+C para parar)[/yellow]\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                now = datetime.now().strftime("%H:%M:%S")
                
                # Pega dados
                ticker, ohlcv = self.get_market_data()
                
                if ticker:
                    price = ticker['last']
                    volume = ticker['quoteVolume']
                    
                    console.print(
                        f"[cyan]{now}[/cyan] | "
                        f"{self.symbol}: [bold]${price:,.2f}[/bold] | "
                        f"Vol: ${volume:,.0f} | "
                        f"Iter: {iteration}"
                    )
                
                # Aguarda 60 segundos
                time.sleep(60)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Bot finalizado pelo usuário[/yellow]")

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
