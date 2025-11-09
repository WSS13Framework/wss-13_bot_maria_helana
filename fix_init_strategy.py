import re

with open('bot.py', 'r') as f:
    content = f.read()

# Procura onde importa RSIVolumeStrategy
if 'from strategies.rsi_volume_strategy import RSIVolumeStrategy' not in content:
    # Adiciona import
    pattern = r'(from data\.normalizer import Normalizer)'
    replacement = r'\1\nfrom strategies.rsi_volume_strategy import RSIVolumeStrategy'
    content = re.sub(pattern, replacement, content)

# Procura onde inicializa o normalizer e adiciona a estratégia logo após
pattern = r'(self\.normalizer = Normalizer\(CONFIG\))'
replacement = r'''\1
        self.rsi_volume_strategy = RSIVolumeStrategy(CONFIG)'''

content = re.sub(pattern, replacement, content)

with open('bot.py', 'w') as f:
    f.write(content)

print("✅ Estratégia adicionada ao __init__!")
