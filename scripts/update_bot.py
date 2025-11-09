#!/usr/bin/env python3
"""
Atualiza bot.py para usar loop_interval_seconds
"""
import re
import sys
from pathlib import Path

def update_bot():
    bot_path = Path("../bot.py")
    
    if not bot_path.exists():
        print("❌ ERRO: bot.py não encontrado!")
        return False
    
    with open(bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procura a linha do sleep
    old_pattern = r"time\.sleep\(CONFIG\.get\('min_time_between_trades',\s*\d+\)\)"
    new_code = "time.sleep(CONFIG.get('loop_interval_seconds', 3600))"
    
    if new_code in content:
        print("✅ bot.py já usa loop_interval_seconds")
        return True
    
    content = re.sub(old_pattern, new_code, content)
    
    # Salva
    with open(bot_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ bot.py atualizado:")
    print("   • Agora usa loop_interval_seconds (1 hora)")
    print("   • Avalia a cada hora, não a cada minuto")
    
    return True

if __name__ == "__main__":
    success = update_bot()
    sys.exit(0 if success else 1)
