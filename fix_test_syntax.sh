#!/bin/bash
# Garante que o script saia imediatamente se um comando falhar
set -e

echo "🔍 INICIANDO TESTE DE SINTAXE DO CÓDIGO PYTHON..."
echo "==================================================="

# Define o caminho do ambiente virtual
VENV_PATH="venv/bin/activate"
# Define o caminho do arquivo a ser compilado
STRATEGY_FILE="strategies/rsi_volume_strategy.py"

# Exibe mensagem de ativação do ambiente virtual
echo "➡️ Ativando ambiente virtual..."
# Ativa o ambiente virtual para que os comandos python usem as libs corretas
source "$VENV_PATH"
echo "✅ Ambiente virtual ativado."

# Exibe mensagem de compilação
echo "➡️ Compilando ${STRATEGY_FILE} para verificar a sintaxe..."
# Usa python -m py_compile para testar a sintaxe do arquivo
# Se houver erro de sintaxe, este comando falhará e o script irá sair devido ao 'set -e'
python -m py_compile "$STRATEGY_FILE"
echo "✅ Compilação bem-sucedida! Nenhuma erro de sintaxe encontrado em ${STRATEGY_FILE}."

echo ""
echo "🎉 SCRIPT 2 CONCLUÍDO: Sintaxe do código validada!"
echo "   Próximo passo: execute 'bash fix_restart_bot.sh'"
