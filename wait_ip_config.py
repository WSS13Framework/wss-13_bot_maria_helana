#!/usr/bin/env python3
import ccxt
import time
from rich.console import Console
from rich.progress import Progress

console = Console()

def test_api_with_ip():
    """Testa API após configuração de IP"""
    
    console.print("🔄 Aguardando configuração de IP na Binance...", style="yellow")
    console.print("📍 IP a ser configurado: 187.120.16.207", style="blue")
    
    # Configuração da API
    config = {
        'apiKey': 'sLzysliWKkvcjdseoIQdkxTKiBKy3lRoeyqE92R5tMSw6Hpf1g8FgVADGlTseuqx',
        'secret': 'MLng5vPjy1G3NS5MCcjIzSjof7HInFfXzOjKhSMv05ES4nbX84gfJSSq81i4UXro',
        'sandbox': False,
        'enableRateLimit': True
    }
    
    max_attempts = 10
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            console.print(f"🧪 Tentativa {attempt}/{max_attempts}...", style="cyan")
            
            exchange = ccxt.binance(config)
            
            # Testar conexão
            balance = exchange.fetch_balance()
            
            console.print("✅ SUCESSO! API wss1101 funcionando!", style="bold green")
            console.print("🎉 IP configurado corretamente na Binance!", style="green")
            
            # Mostrar informações básicas
            console.print(f"📊 Conta conectada com sucesso", style="blue")
            return True
            
        except ccxt.AuthenticationError as e:
            if "IP" in str(e) or "2015" in str(e):
                console.print(f"⏳ IP ainda não configurado... (tentativa {attempt})", style="yellow")
                console.print("💡 Configure o IP 187.120.16.207 na Binance e aguarde...", style="blue")
            else:
                console.print(f"❌ Erro de autenticação: {e}", style="red")
                
        except Exception as e:
            console.print(f"❌ Erro: {e}", style="red")
        
        if attempt < max_attempts:
            console.print("⏱️  Aguardando 30 segundos...", style="yellow")
            time.sleep(30)
        
        attempt += 1
    
    console.print("❌ Não foi possível conectar após todas as tentativas", style="red")
    console.print("💡 Verifique se o IP 187.120.16.207 foi adicionado corretamente", style="yellow")
    return False

if __name__ == "__main__":
    test_api_with_ip()
