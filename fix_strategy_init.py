with open('bot.py', 'r') as f:
    lines = f.readlines()

# Encontra e substitui o bloco inteiro
new_lines = []
i = 0
while i < len(lines):
    if 'self.strategy: RSIVolumeStrategy = RSIVolumeStrategy(' in lines[i]:
        # Substitui todo o bloco por uma única linha
        new_lines.append('        self.strategy: RSIVolumeStrategy = RSIVolumeStrategy(self.config)\n')
        # Pula todas as linhas até o fechamento do parêntesis
        i += 1
        while i < len(lines) and ')' not in lines[i]:
            i += 1
        i += 1  # Pula a linha com ')'
    else:
        new_lines.append(lines[i])
        i += 1

with open('bot.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Estratégia corrigida!")
