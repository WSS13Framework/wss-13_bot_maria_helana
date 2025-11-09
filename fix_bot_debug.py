import re

with open('bot.py', 'r') as f:
    content = f.read()

# Procura o bloco onde pega ticker e ohlcv
pattern = r"(if ticker and ohlcv:)"

replacement = r"""if ticker and ohlcv:
                    console.print("[cyan]   🔍 DEBUG: Ticker e OHLCV recebidos[/cyan]")"""

content = re.sub(pattern, replacement, content, count=1)

# Adiciona debug antes da normalização
pattern2 = r"(# 📊 NORMALIZAÇÃO DOS DADOS)"

replacement2 = r"""console.print("[cyan]   🔍 DEBUG: Iniciando normalização...[/cyan]")
                    # 📊 NORMALIZAÇÃO DOS DADOS"""

content = re.sub(pattern2, replacement2, content, count=1)

# Adiciona debug após normalização
pattern3 = r"(normalized_data = self\.normalizer\.process\(ohlcv, ticker\))"

replacement3 = r"""\1
                    console.print(f"[cyan]   🔍 DEBUG: Normalização completa! RSI={normalized_data.get('rsi_norm', 'N/A')}[/cyan]")"""

content = re.sub(pattern3, replacement3, content, count=1)

with open('bot.py', 'w') as f:
    f.write(content)

print("✅ Debug detalhado adicionado!")
