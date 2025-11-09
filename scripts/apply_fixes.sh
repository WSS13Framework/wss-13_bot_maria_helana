#!/bin/bash
# 🤖 Maria Helena - Auto-Fix Script
# Aplica todos os ajustes automaticamente

set -e  # Para se der erro

echo "🤖 Maria Helena - Aplicando Ajustes Profissionais..."
echo "=================================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Backup
echo -e "${YELLOW}📦 Passo 1/5: Criando backup...${NC}"
bash backup_configs.sh
echo -e "${GREEN}✅ Backup criado em backups/$(date +%Y%m%d_%H%M%S)/${NC}"
echo ""

# 2. Atualiza config.py
echo -e "${YELLOW}⚙️  Passo 2/5: Ajustando config.py...${NC}"
python3 update_config.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ config.py atualizado${NC}"
else
    echo -e "${RED}❌ Erro ao atualizar config.py${NC}"
    exit 1
fi
echo ""

# 3. Atualiza estratégia
echo -e "${YELLOW}🎯 Passo 3/5: Ajustando estratégia RSI+Volume...${NC}"
python3 update_strategy.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Estratégia atualizada${NC}"
else
    echo -e "${RED}❌ Erro ao atualizar estratégia${NC}"
    exit 1
fi
echo ""

# 4. Atualiza bot.py
echo -e "${YELLOW}🤖 Passo 4/5: Ajustando bot.py...${NC}"
python3 update_bot.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ bot.py atualizado${NC}"
else
    echo -e "${RED}❌ Erro ao atualizar bot.py${NC}"
    exit 1
fi
echo ""

# 5. Verifica mudanças
echo -e "${YELLOW}🔍 Passo 5/5: Verificando mudanças...${NC}"
python3 verify_changes.py
echo ""

echo "=================================================="
echo -e "${GREEN}🎉 TODOS OS AJUSTES APLICADOS COM SUCESSO!${NC}"
echo ""
echo "📋 Próximos passos:"
echo "   1. cd ~/Projects/maria-helena-bot"
echo "   2. source venv/bin/activate"
echo "   3. python bot.py"
echo ""
echo "💡 Deixe rodar por 2-4 horas e monitore os logs!"
echo "=================================================="
