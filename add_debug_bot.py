import re

with open('bot.py', 'r') as f:
    content = f.read()

# Procura a linha após normalizer.process
pattern = r"(normalized_data = self\.normalizer\.process\(ohlcv, ticker\))"

replacement = r"""\1
                    console.print(f"[cyan]   🔍 Dados normalizados: RSI={normalized_data['rsi_norm']:.4f}, Vol={normalized_data['volume_norm']:.4f}[/cyan]")"""

content = re.sub(pattern, replacement, content)

with open('bot.py', 'w') as f:
    f.write(content)

print("✅ Debug adicionado ao bot.py")
