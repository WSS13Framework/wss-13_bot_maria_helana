#!/usr/bin/env python3
# ARQUIVO: maria_helena_migrator.py
# FUNÇÃO NO ECOSSISTEMA MARIA HELENA:
# Realiza a migração de dados (ETL) de um arquivo CSV legado
# para o novo banco de dados SQLite v2.0.

import csv
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('MariaHelena.Migrator')

# Caminhos dos arquivos
CSV_SOURCE_PATH = Path('./maria-helena-scripts/maria_helena_data.csv')
DB_DEST_PATH = Path.home() / 'maria-helena' / 'data' / 'maria_helena_signals.db'

# Mapeamento de colunas CSV -> DB
# Formato: 'coluna_db': 'coluna_csv'
COLUMN_MAPPING = {
    'price': 'close',
    'volume': 'volume',
    'rsi': 'rsi_14',
    'bb_upper': 'bb_upper',
    'bb_lower': 'bb_lower',
    'macd': 'macd',
    'macd_signal': 'macd_signal',
    'obv': 'obv',
}

# ==========================================
# SCRIPT DE MIGRAÇÃO
# ==========================================

def safe_float(value: str, default: float = 0.0) -> float:
    """Converte uma string para float de forma segura, tratando valores vazios."""
    if value is None or value.strip() == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def migrate_data():
    """Executa o processo de migração de dados."""
    logger.info("=" * 60)
    logger.info("🚀 Maria Helena - Iniciando Migração de Dados (ETL)")
    logger.info("=" * 60)
    
    # 1. Validar arquivos de origem e destino
    if not CSV_SOURCE_PATH.exists():
        logger.error(f"❌ Arquivo de origem não encontrado: {CSV_SOURCE_PATH}")
        return
    if not DB_DEST_PATH.exists():
        logger.error(f"❌ Banco de dados de destino não encontrado: {DB_DEST_PATH}")
        logger.error("   Execute o 'maria_helena_database_creator.py' primeiro.")
        return

    logger.info(f"Fonte: {CSV_SOURCE_PATH}")
    logger.info(f"Destino: {DB_DEST_PATH}")

    try:
        # 2. Conectar ao banco de dados de destino
        conn = sqlite3.connect(DB_DEST_PATH)
        cursor = conn.cursor()
        
        # 3. Ler o arquivo CSV
        with open(CSV_SOURCE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            records_to_insert = []
            total_rows = 0
            
            for row in reader:
                total_rows += 1
                
                # --- FASE DE TRANSFORMAÇÃO (T do ETL) ---
                
                # Transformar timestamp de milissegundos para segundos
                timestamp_ms = safe_float(row.get('openTime', '0'))
                if timestamp_ms == 0:
                    logger.warning(f"Linha {total_rows} ignorada: timestamp inválido.")
                    continue
                
                new_record = {
                    'asset': 'BTCUSDT',  # Assumindo o ativo padrão
                    'timestamp': int(timestamp_ms / 1000),
                    'trend': 'UNKNOWN' # Preenchendo dados não existentes
                }
                
                # Mapear e converter colunas
                for db_col, csv_col in COLUMN_MAPPING.items():
                    new_record[db_col] = safe_float(row.get(csv_col))
                
                # Adicionar à lista para inserção em lote
                records_to_insert.append(new_record)

            logger.info(f"🔎 {len(records_to_insert)} de {total_rows} registros lidos e transformados.")

            # 4. Inserir os dados em lote (LOAD do ETL)
            if records_to_insert:
                cursor.executemany("""
                    INSERT OR IGNORE INTO market_analysis_v2 
                    (asset, timestamp, price, volume, rsi, bb_upper, bb_lower, macd, macd_signal, obv, trend)
                    VALUES (:asset, :timestamp, :price, :volume, :rsi, :bb_upper, :bb_lower, :macd, :macd_signal, :obv, :trend)
                """, records_to_insert)
                
                conn.commit()
                logger.info(f"✅ {cursor.rowcount} novos registros inseridos no banco de dados.")
            else:
                logger.warning("⚠️ Nenhum registro novo para inserir.")

    except sqlite3.Error as e:
        logger.error(f"❌ Erro de SQLite durante a migração: {e}")
        conn.rollback()
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("�� Conexão com o banco de dados fechada.")

    logger.info("=" * 60)
    logger.info("🏁 Migração de dados concluída.")
    logger.info("=" * 60)


if __name__ == "__main__":
    migrate_data()
