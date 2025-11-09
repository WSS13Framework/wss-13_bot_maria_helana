#!/bin/bash
# Garante que o script saia imediatamente se um comando falhar
set -e

echo "🚀 INICIANDO REINICIALIZAÇÃO DO BOT MARIA HELENA..."
echo "==================================================="

# Define o nome da sessão screen
SCREEN_NAME="maria-helena"
# Define o comando para iniciar o bot
BOT_COMMAND="cd ~/Projects/maria-helena-bot && source venv/bin/activate && python bot.py"
# Define o caminho do log do bot
BOT_LOG="bot.log"

# Exibe mensagem de parada do bot
echo "➡️ Parando qualquer instância anterior do bot..."
echo "✅ Comandos de parada enviados."

# Exibe mensagem de espera
echo "⏳ Aguardando 2 segundos para garantir que os processos antigos sejam encerrados..."
# Pausa o script por 2 segundos
sleep 2

# Exibe mensagem de início do bot
echo "➡️ Iniciando o bot em uma nova sessão 'screen'..."
# Inicia o bot em uma nova sessão screen (-dmS detached, nomeada, rodando o comando)
screen -dmS "$SCREEN_NAME" bash -c "$BOT_COMMAND"
echo "✅ Bot Maria Helena iniciado na sessão screen '$SCREEN_NAME'."

# Exibe mensagem de espera
echo "⏳ Aguardando 5 segundos para o bot iniciar e gerar logs..."
# Pausa o script por 5 segundos
sleep 5

# Exibe as últimas linhas do log do bot
echo ""
echo "📊 Últimas 15 linhas do ${BOT_LOG}:"
echo "---------------------------------------------------------"
# Verifica se o arquivo de log existe antes de tentar lê-lo
if [ -f "$BOT_LOG" ]; then
    # Exibe as últimas 15 linhas do arquivo de log
else
    echo "⚠️ Arquivo de log '${BOT_LOG}' ainda não encontrado. O bot pode estar inicializando."
    echo "   Use 'screen -r ${SCREEN_NAME}' para verificar."
fi

echo ""
echo "🎉 SCRIPT 3 CONCLUÍDO: Bot Maria Helena reiniciado!"
echo ""
echo "📌 Para ver os logs em tempo real, digite: 'screen -r ${SCREEN_NAME}'"
echo "   Para desanexar (manter rodando em segundo plano): Pressione 'Ctrl+A', depois 'D'"
echo "   Para acompanhar os sinais, digite: 'tail -f bot.log | grep \"SINAL\"'"
