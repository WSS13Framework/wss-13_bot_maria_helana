#!/usr/bin/env python3
"""
Verifica se as mudanças foram aplicadas corretamente
"""
import sys
from pathlib import Path

def verify_changes():
    print("🔍 Verificando mudanças...\n")
    
    all_ok = True
    
    # === VERIFICA CONFIG.PY ===
    config_path = Path("../config.py")
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    checks = [
        ("'rsi_oversold': 40", "✅ RSI oversold = 40"),
        ("'rsi_overbought': 60", "✅ RSI overbought = 60"),
        ("'volume_threshold': 0.60", "✅ Volume threshold = 0.60"),
        ("'loop_interval_seconds'", "✅ Loop interval configurado"),
    ]
    
    print("📄 config.py:")
    for check, msg in checks:
        if check in config_content:
            print(f"   {msg}")
        else:
            print(f"   ❌ {check} NÃO encontrado")
            all_ok = False
    print()
    
    # === VERIFICA ESTRATÉGIA ===
    strategy_path = Path("../strategies/rsi_volume_strategy.py")
    with open(strategy_path, 'r') as f:
        strategy_content = f.read()
    
    print("🎯 rsi_volume_strategy.py:")
    if 'console.print(f"[dim]   📊 RSI:' in strategy_content:
        print("   ✅ Debug logs adicionados")
    else:
        print("   ❌ Debug logs NÃO encontrados")
        all_ok = False
    print()
    
    # === VERIFICA BOT.PY ===
    bot_path = Path("../bot.py")
    with open(bot_path, 'r') as f:
        bot_content = f.read()
    
    print("🤖 bot.py:")
    if "CONFIG.get('loop_interval_seconds'" in bot_content:
        print("   ✅ Loop interval configurado")
    else:
        print("   ❌ Loop interval NÃO configurado")
        all_ok = False
    print()
    
    # === RESUMO ===
    if all_ok:
        print("=" * 50)
        print("🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
        print("=" * 50)
        print("\n📊 Resumo das mudanças:")
        print("   1. RSI: 30/70 → 40/60 (mais sinais)")
        print("   2. Volume: 0.70 → 0.60 (menos restritivo)")
        print("   3. Loop: 60s → 3600s (avalia a cada hora)")
        print("   4. Debug: Mostra RSI/Volume a cada iteração")
        print("\n💡 Maria Helena está pronta para trabalhar!")
    else:
        print("=" * 50)
        print("⚠️  ALGUMAS VERIFICAÇÕES FALHARAM")
        print("=" * 50)
        print("\nRevise os arquivos manualmente ou rode o script novamente.")
    
    return all_ok

if __name__ == "__main__":
    success = verify_changes()
    sys.exit(0 if success else 1)
