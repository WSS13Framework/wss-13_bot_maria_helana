#!/bin/bash
# 📦 Backup dos arquivos antes de modificar

BACKUP_DIR="../backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Arquivos a fazer backup
FILES=(
    "../config.py"
    "../bot.py"
    "../strategies/rsi_volume_strategy.py"
)

echo "Criando backup em: $BACKUP_DIR"

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        echo "  ✅ $(basename $file) salvo"
    else
        echo "  ⚠️  $(basename $file) não encontrado"
    fi
done

echo ""
echo "Backup completo!"
