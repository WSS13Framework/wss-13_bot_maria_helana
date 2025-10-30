#!/usr/bin/env python3
"""
Teste específico para API wss1101
WSS+13 System by Marcos Sea
"""

import ccxt
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import time

console = Console()

def load_wss1101_config():
    """Carrega configuração wss1101"""
    try:
        config_path = os.path.expanduser('~/.binance_config')
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
        return config
    except Exception as e:
        console.print(f"❌ Erro ao carregar config: {e}", style="red")
        return None

def test_wss1101_connection():
    """Testa conexão específica wss1101"""
    
    console.print(Panel("🔧 Testando API wss1101", style="bold blue"))
    
    config = load_wss1101_config()
    if not config:
        return False
    
    try:
        # Configurar exchange com credenciais wss1101
        exchange = ccxt.binance({
            'apiKey': config['BINANCE_API_KEY'],
            'secret': config['BINANCE_SECRET_KEY'],
            'sandbox': False,  # Produção
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # Especificar tipo spot
            }
        })
        
        console.print("🔄 Testando conexão...", style="yellow")
        
        # Teste 1: Verificar status da API
        try:
            exchange.load_markets()
            console.print("✅ Mercados carregados", style="green")
        except Exception as e:
            console.print(f"❌ Erro ao carregar mercados: {e}", style="red")
            return False
        
        # Teste 2: Buscar informações da conta
        try:
            account_info = exchange.fetch_balance()
            console.print("✅ Informações da conta obtidas", style="green")
            
            # Mostrar saldo
            table = Table(title="💰 Saldo da Conta wss1101")
            table.add_column("Asset", style="cyan")
            table.add_column("Free", style="green")
            table.add_column("Used", style="yellow")
            table.add_column("Total", style="blue")
            
            assets_shown = 0
            for asset, balance in account_info.items():
                if isinstance(balance, dict) and balance.get('total', 0) > 0:
                    table.add_row(
                        asset,
                        f"{balance.get('free', 0):.8f}",
                        f"{balance.get('used', 0):.8f}",
                        f"{balance.get('total', 0):.8f}"
                    )
                    assets_shown += 1
                    if assets_shown >= 10:  # Limitar exibição
                        break
            
            if assets_shown > 0:
                console.print(table)
            else:
                console.print("💡 Conta sem saldos ou apenas com valores muito pequenos", style="yellow")
            
        except Exception as e:
            console.print(f"⚠️  Erro ao buscar saldo: {e}", style="yellow")
            console.print("💡 Pode ser restrição de permissão da API", style="blue")
        
        # Teste 3: Buscar dados de mercado (público)
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
            console.print(f"\n📈 BTC/USDT: ${ticker['last']:,.2f}", style="bold green")
            console.print(f"📊 Volume 24h: {ticker['baseVolume']:,.2f} BTC", style="blue")
            console.print(f"📈 Variação 24h: {ticker['percentage']:.2f}%", style="cyan")
        except Exception as e:
            console.print(f"❌ Erro ao buscar ticker: {e}", style="red")
        
        # Teste 4: Verificar permissões
        console.print("\n🔐 Verificando permissões da API:", style="yellow")
        
        # Tentar operações que requerem diferentes permissões
        permissions = {
            "Leitura de Conta": False,
            "Dados de Mercado": False,
            "Trading Spot": False
        }
        
        try:
            exchange.fetch_balance()
            permissions["Leitura de Conta"] = True
        except:
            pass
        
        try:
            exchange.fetch_ticker('BTC/USDT')
            permissions["Dados de Mercado"] = True
        except:
            pass
        
        # Mostrar permissões
        perm_table = Table(title="🔑 Permissões da API wss1101")
        perm_table.add_column("Permissão", style="cyan")
        perm_table.add_column("Status", style="green")
        
        for perm, status in permissions.items():
            status_icon = "✅" if status else "❌"
            perm_table.add_row(perm, status_icon)
        
        console.print(perm_table)
        
        console.print("\n🎉 Teste da API wss1101 concluído!", style="bold green")
        return True
        
    except ccxt.AuthenticationError as e:
        console.print(f"❌ Erro de autenticação: {e}", style="red")
        console.print("💡 Verifique se a API key wss1101 está ativa", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Erro geral: {e}", style="red")
        return False

if __name__ == "__main__":
    test_wss1101_connection()
