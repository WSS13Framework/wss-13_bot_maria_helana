#!/usr/bin/env python3
"""
Atualiza config.py com os novos parâmetros
"""
import re
import sys
from pathlib import Path

def update_config():
    config_path = Path("../config.py")
    
    if not config_path.exists():
        print("❌ ERRO: config.py não encontrado!")
        return False
    
    # Lê conteúdo
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup do original
    original_content = content
    
    # === AJUSTE 1: RSI Oversold ===
    content = re.sub(
        r"'rsi_oversold':\s*30",
        "'rsi_oversold': 40",
        content
    )
    
    # === AJUSTE 2: RSI Overbought ===
    content = re.sub(
        r"'rsi_overbought':\s*70",
        "'rsi_overbought': 60",
        content
    )
    
    # === AJUSTE 3: Volume Threshold ===
    content = re.sub(
        r"'volume_threshold':\s*0\.70",
        "'volume_threshold': 0.60",
        content
    )
    
    # === AJUSTE 4: Adiciona loop_interval_seconds (se não existir) ===
    if "'loop_interval_seconds'" not in content:
        # Procura a seção de LIMITES OPERACIONAIS
        limites_section = re.search(
            r"(# === LIMITES OPERACIONAIS ===.*?'max_consecutive_losses':\s*\d+,)",
            content,
            re.DOTALL
        )
        
        if limites_section:
            new_section = limites_section.group(1) + "\n    'loop_interval_seconds': 3600,  # Avalia a cada 1 hora"
            content = content.replace(limites_section.group(1), new_section)
    
    # Verifica se houve mudanças
    if content == original_content:
        print("⚠️  Nenhuma mudança necessária em config.py")
        return True
    
    # Salva
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ config.py atualizado:")
    print("   • rsi_oversold: 30 → 40")
    print("   • rsi_overbought: 70 → 60")
    print("   • volume_threshold: 0.70 → 0.60")
    print("   • loop_interval_seconds: 3600 (adicionado)")
    
    return True

if __name__ == "__main__":
    success = update_config()
    sys.exit(0 if success else 1)
