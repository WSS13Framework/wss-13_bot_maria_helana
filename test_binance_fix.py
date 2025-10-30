#!/usr/bin/env python3
import ccxt
import os
from rich.console import Console
from rich.table import Table

console = Console()

def load_api_config():
    """Carrega configurações da API"""
    try:
        config_path = os.path.expanduser('~/.binance_config')
        if not os.path.exists(config_path):
            console.print("❌ Arquivo de configuração não encontrado!", style="red")
            console.print("💡 Execute: ./fix_binance_api.sh primeiro", style="yellow")
            return None
            
        with open(config_path, 'r') as f:
            config = {}
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
            return config
    except Exception as e:
        console.print(f"❌ Erro ao ler configuração: {e}", style="red")
        return None

def test_binance_connection():
    """Testa conexão com Binance"""
    config = load_api_config()
    if not config:
        return False
    
    # Verificar se as chaves não são placeholder
    api_key = config.get('BINANCE_API_KEY', '')
    if api_key == 'sua_api_key_aqui' or not api_key:
        console.print("⚠️  Configure suas API keys reais!", style="yellow")
        console.print("📝 Edite: nano ~/.binance_config", style="blue")
        return False
    
    try:
        # Configurar exchange
        exchange = ccxt.binance({
            'apiKey': config.get('BINANCE_API_KEY'),
            'secret': config.get('BINANCE_SECRET_KEY'),
            'sandbox': config.get('BINANCE_TESTNET', 'false').lower() == 'true',
            'enableRateLimit': True,
        })
        
        # Testar conexão básica
        exchange.load_markets()
        console.print("✅ Binance API conectada com sucesso!", style="green")
        return True
        
    except ccxt.AuthenticationError as e:
        console.print(f"❌ Erro de autenticação: {e}", style="red")
        console.print("💡 Verifique suas API keys", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="red")
        return False

def show_status():
    """Mostra status do sistema"""
    table = Table(title="🎯 Status WSS+13")
    table.add_column("Componente", style="cyan")
    table.add_column("Status", style="green")
    
    # Testar imports
    try:
        import ccxt, pandas, talib, rich
        table.add_row("Python Libs", "✅ OK")
    except ImportError as e:
        table.add_row("Python Libs", f"❌ {e}")
    
    # Testar API config
    config = load_api_config()
    if config and config.get('BINANCE_API_KEY') != 'sua_api_key_aqui':
        table.add_row("API Config", "✅ Configurado")
    else:
        table.add_row("API Config", "⚠️  Pendente")
    
    console.print(table)

if __name__ == "__main__":
    console.print("🔄 Testando sistema WSS+13...", style="yellow")
    show_status()
    test_binance_connection()
