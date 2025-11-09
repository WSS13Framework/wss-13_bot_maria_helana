#!/usr/bin/env python3
"""
Atualiza rsi_volume_strategy.py para adicionar debug logs
"""
import re
import sys
from pathlib import Path

def update_strategy():
    strategy_path = Path("../strategies/rsi_volume_strategy.py")
    
    if not strategy_path.exists():
        print("❌ ERRO: rsi_volume_strategy.py não encontrado!")
        return False
    
    with open(strategy_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se já tem o log de debug
    if 'console.print(f"[dim]   📊 RSI:' in content:
        print("✅ Debug logs já existem na estratégia")
        return True
    
    # Procura a linha onde adicionar o log
    # Após: trend = normalized_data.get('trend', 'neutral')
    pattern = r"(trend = normalized_data\.get\('trend', 'neutral'\)\s*\n)"
    
    debug_code = r"""\1        
        # 🔍 DEBUG: Mostra valores normalizados
        console.print(f"[dim]   📊 RSI: {rsi:.4f} ({rsi*100:.1f}) | "
                      f"Vol: {volume:.4f} | Trend: {trend}[/dim]")
        
"""
    
    content = re.sub(pattern, debug_code, content)
    
    # Salva
    with open(strategy_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Estratégia atualizada:")
    print("   • Debug logs adicionados")
    print("   • Agora mostra RSI e Volume a cada iteração")
    
    return True

if __name__ == "__main__":
    success = update_strategy()
    sys.exit(0 if success else 1)
