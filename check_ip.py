#!/usr/bin/env python3
import requests
from rich.console import Console
from rich.table import Table

console = Console()

def check_current_ip():
    """Verifica IP atual e configuração"""
    
    console.print("🌐 Verificando configuração de IP...", style="yellow")
    
    try:
        # Verificar IP público atual
        response = requests.get('https://httpbin.org/ip', timeout=10)
        current_ip = response.json()['origin']
        
        # Verificar IP via outro serviço
        response2 = requests.get('https://api.ipify.org?format=json', timeout=10)
        current_ip2 = response2.json()['ip']
        
        table = Table(title="📍 Informações de IP")
        table.add_column("Serviço", style="cyan")
        table.add_column("IP Detectado", style="green")
        table.add_column("Status", style="yellow")
        
        table.add_row("httpbin.org", current_ip, "✅ Ativo")
        table.add_row("ipify.org", current_ip2, "✅ Ativo")
        
        console.print(table)
        
        if current_ip == current_ip2:
            console.print(f"✅ IP consistente: {current_ip}", style="green")
        else:
            console.print("⚠️ IPs diferentes detectados!", style="yellow")
        
        # Verificar se é IP dinâmico
        console.print("\n🔍 Análise do IP:", style="blue")
        
        if current_ip.startswith(('192.168.', '10.', '172.')):
            console.print("❌ IP privado detectado - usando NAT/Proxy", style="red")
        else:
            console.print("✅ IP público válido", style="green")
            
        return current_ip
        
    except Exception as e:
        console.print(f"❌ Erro ao verificar IP: {e}", style="red")
        return None

def check_binance_ip_config():
    """Verifica configuração de IP na Binance"""
    
    console.print("\n�� Configuração recomendada para Binance:", style="blue")
    
    recommendations = [
        "1. Acesse: https://www.binance.com/en/my/settings/api-management",
        "2. Clique na sua API key wss1101",
        "3. Vá em 'Edit restrictions'",
        "4. Configure 'Restrict access to trusted IPs only'",
        "5. Adicione seu IP atual",
        "6. Salve as alterações"
    ]
    
    for rec in recommendations:
        console.print(f"   {rec}", style="cyan")

if __name__ == "__main__":
    current_ip = check_current_ip()
    check_binance_ip_config()
    
    if current_ip:
        console.print(f"\n💡 Adicione este IP na Binance: {current_ip}", style="bold yellow")
