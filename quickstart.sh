#!/bin/bash
# Diagnostica inconsistências no threshold de RSI
set -e

echo "🔍 DIAGNÓSTICO RSI THRESHOLD"
echo "======================================"

CONFIG_FILE="config.py"
STRATEGY_FILE="strategies/rsi_volume_strategy.py"
BOT_FILE="bot.py"

echo ""
echo "📍 Procurando config.py..."
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ config.py não encontrado!"
    exit 1
fi

# Extrai valor do rsi_overbought
echo "✅ Valor em config.py: $RSI_CONFIG"

if [ "$RSI_CONFIG" -eq 70 ]; then
    echo "   → Esperado: 70 ✅"
elif [ "$RSI_CONFIG" -eq 60 ]; then
    echo "   → ERRO: Está em 60, deveria ser 70! ❌"
else
    echo "   → AVISO: Valor inesperado: $RSI_CONFIG ⚠️"
fi

echo ""
echo "📍 Procurando em rsi_volume_strategy.py..."
if [ -f "$STRATEGY_FILE" ]; then
    echo "Referências encontradas:"
    echo "$STRATEGY_REF"
else
    echo "❌ Arquivo não encontrado: $STRATEGY_FILE"
fi

echo ""
echo "📍 Verificando chamada de _check_sell_conditions..."
BOT_CALL=$(grep "_check_sell_conditions" "$BOT_FILE" 2>/dev/null | head -2)
if echo "$BOT_CALL" | grep -q "rsi, trend"; then
    echo "✅ Está passando (rsi, trend) corretamente!"
else
    echo "❌ NÃO está passando trend! Precisa corrigir:"
    echo "   Atual: $(echo "$BOT_CALL" | grep -oE 'self\._check_sell_conditions\([^)]+\)')"
    echo "   Deveria: self._check_sell_conditions(rsi, trend)"
fi

echo ""
echo "======================================"
echo "✅ Diagnóstico completo!"#!/bin/bash
# Corrige a precisão da estratégia RSI
set -e

echo "🔧 CORRIGINDO ESTRATÉGIA RSI"
echo "======================================"

STRATEGY_FILE="strategies/rsi_volume_strategy.py"
BACKUP_FILE="${STRATEGY_FILE}.backup"

# Faz backup
echo "📦 Criando backup..."
cp "$STRATEGY_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"

echo ""
echo "🔨 Corrigindo _check_sell_conditions..."

# Cria versão corrigida usando heredoc
python3 << 'EOFPYTHON'
import re

file_path = "strategies/rsi_volume_strategy.py"

with open(file_path, 'r') as f:
    content = f.read()

# Passo 1: Corrige assinatura do método
old_signature = r'def _check_sell_conditions\(self, rsi\):'
new_signature = 'def _check_sell_conditions(self, rsi, trend):'

content = re.sub(old_signature, new_signature, content)
print("✅ Assinatura do método atualizada")

# Passo 2: Substitui o corpo do método
# A regex precisa ser mais específica para evitar substituir além do corpo da função
# Vamos encontrar o corpo da função _check_sell_conditions
# O padrão regex usado originalmente está muito solto e pode pegar mais que o desejado.
# Ajuste para ser mais preciso, capturando de 'def _check_sell_conditions(...):' até 'return False' ou o início da próxima função/classe.

# Primeiro, encontra o bloco completo da função _check_sell_conditions
# e então substitui seu conteúdo interno.
# Esta abordagem é mais robusta que o re.sub direto de blocos multi-linha.

func_start_pattern = r"def _check_sell_conditions\(self, rsi, trend\):"

match = re.search(f"{func_start_pattern}.*?{func_end_pattern}", content, re.DOTALL)

if match:
    # Conteúdo atual da função
    current_func_content = match.group(0)

    # Novo corpo da função com o cabeçalho já corrigido
    new_body_content = '''def _check_sell_conditions(self, rsi, trend):
        """Condições de venda com proteção por tendência"""
        
        if trend == 'up':
            # Em uptrend, exige RSI muito alto
            return rsi > 0.75
        elif trend == 'neutral':
            # Em neutro, usa threshold normal
            return rsi > 0.70
        else:  # downtrend
            # Em downtrend, vende quando overbought
            return rsi > 0.65
        
        return False'''
    
    # Substitui o conteúdo antigo da função pelo novo
    content = content.replace(current_func_content, new_body_content)
    print("✅ Corpo do método atualizado")
else:
    print("❌ Não foi possível encontrar a função _check_sell_conditions para substituir o corpo.")


with open(file_path, 'w') as f:
    f.write(content)

print("✅ Arquivo gravado com sucesso")
EOFPYTHON

echo ""
echo "🧪 Validando sintaxe Python..."

echo ""
echo "======================================"
echo "✅ Estratégia corrigida!"
#!/bin/bash
# Valida as mudanças sem quebrar o bot
set -e

echo "✅ VALIDANDO MUDANÇAS"
echo "======================================"

echo ""
echo "🧪 Teste 1: Compilar Python files..."
python3 -m py_compile strategies/rsi_volume_strategy.py && echo "   ✅ rsi_volume_strategy.py OK"
python3 -m py_compile bot.py && echo "   ✅ bot.py OK"
python3 -m py_compile config.py && echo "   ✅ config.py OK"

echo ""
echo "🧪 Teste 2: Verificar imports..."
python3 << 'EOFPYTHON'
try:
    import sys
    sys.path.insert(0, '/home/sea/Projects/maria-helena-bot')
    from config import CONFIG
    from strategies.rsi_volume_strategy import RSIVolumeStrategy
    print("   ✅ Imports OK")
except Exception as e:
    print(f"   ❌ Erro no import: {e}")
    exit(1)
EOFPYTHON

echo ""
echo "🧪 Teste 3: Verificar assinatura do método..."
python3 << 'EOFPYTHON'
import inspect
from strategies.rsi_volume_strategy import RSIVolumeStrategy

method = RSIVolumeStrategy._check_sell_conditions
sig = inspect.signature(method)
params = list(sig.parameters.keys())

expected = ['self', 'rsi', 'trend']
if params == expected:
    print(f"   ✅ Assinatura correta: {params}")
else:
    print(f"   ❌ Assinatura incorreta!")
    print(f"      Esperado: {expected}")
    print(f"      Atual: {params}")
    exit(1)
EOFPYTHON

echo ""
echo "======================================"
echo "✅ Todas as validações passaram!"
#!/bin/bash
# Deploy final e reinício do bot
set -e

echo "🚀 DEPLOY FINAL"
echo "======================================"

BOT_PROCESS="maria-helena"
BOT_FILE="bot.py"
LOG_FILE="bot.log"

echo ""
echo "🔍 Procurando processo antigo..."
if pgrep -f "$BOT_FILE" > /dev/null; then
    echo "   ⏹️  Matando processo antigo..."
    sleep 2
    echo "   ✅ Processo antigo encerrado"
else
    echo "   ℹ️  Nenhum processo em execução"
fi

echo ""
echo "🟢 Iniciando novo bot em screen..."

# Cria ou anexa screen com nome maria-helena
screen -dmS "$BOT_PROCESS" bash -c "
    cd /home/sea/Projects/maria-helena-bot
    source venv/bin/activate
    python bot.py 2>&1 | tee -a $LOG_FILE
"

sleep 2

# Verifica se iniciou
if screen -list | grep -q "$BOT_PROCESS"; then
    echo "   ✅ Screen iniciada: $BOT_PROCESS"
    echo ""
    echo "📋 Logs em tempo real:"
    echo "   screen -r $BOT_PROCESS"
    echo ""
    echo "   Para desatar: Ctrl+A, depois D"
    echo ""
    echo "📊 Arquivo de log:"
    echo "   tail -f $LOG_FILE"
else
    echo "   ❌ Erro ao iniciar screen!"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Bot deployado e rodando!"
#!/bin/bash
# Executa toda a correção automaticamente
set -e

echo "⚡ QUICKSTART - CORREÇÃO AUTOMÁTICA"
echo "======================================"

# Altere este caminho se o seu projeto não estiver em /home/sea/Projects/maria-helena-bot

echo ""
echo "📋 PASSO 1/4: Diagnóstico"
bash diagnose_rsi_threshold.sh

echo ""
echo "⏸️  Pressione ENTER para continuar..."
read

echo ""
echo "📋 PASSO 2/4: Corrigir Estratégia"
bash fix_strategy_precision.sh

echo ""
echo "⏸️  Pressione ENTER para continuar..."
read

echo ""
echo "📋 PASSO 3/4: Validar Mudanças"
bash validate_changes.sh

echo ""
echo "⏸️  Pressione ENTER para continuar..."
read

echo ""
echo "📋 PASSO 4/4: Deploy do Bot"
bash deploy_updated_bot.sh

echo ""
echo "======================================"
echo "🎉 TUDO COMPLETO!"
echo "⏰ Acompanhe os logs por 24-48h"
echo "======================================"
