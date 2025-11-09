#!/usr/bin/env python3
"""
Maria Helena - Database Creator v2.0
Cria e gerencia o banco de dados de análise de mercado com melhorias de performance e integridade.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# ==========================================
# CONFIGURAÇÃO
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('MariaHelena.DB')

# Usar Path ao invés de string
DB_DIR = Path.home() / 'maria-helena' / 'data'
DB_PATH = DB_DIR / 'maria_helena_signals.db'

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def ensure_directory() -> bool:
    """Garante que o diretório existe"""
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Diretório verificado: {DB_DIR}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar diretório: {e}")
        return False


def create_tables(conn: sqlite3.Connection) -> bool:
    """Cria todas as tabelas necessárias com índices e constraints"""
    cursor = conn.cursor()
    
    try:
        # Tabela principal de análise de mercado
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_analysis_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                timestamp INTEGER NOT NULL,  -- Unix timestamp para melhor performance
                price REAL NOT NULL CHECK(price > 0),
                volume REAL CHECK(volume >= 0),
                
                -- Indicadores técnicos
                rsi REAL CHECK(rsi BETWEEN 0 AND 100),
                bb_upper REAL,
                bb_lower REAL,
                bb_middle REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                sma REAL,
                obv REAL,
                
                -- Análise
                trend TEXT CHECK(trend IN ('BULLISH', 'BEARISH', 'NEUTRAL', 'UNKNOWN')),
                signal TEXT CHECK(signal IN ('BUY', 'SELL', 'HOLD', NULL)),
                confidence REAL CHECK(confidence BETWEEN 0 AND 1),
                
                -- Metadados
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                
                -- Constraint de unicidade
                UNIQUE(asset, timestamp)
            )
        """)
        logger.info("✅ Tabela 'market_analysis_v2' criada/verificada")
        
        # Criar índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_asset_timestamp 
            ON market_analysis_v2(asset, timestamp DESC)
        """)
        logger.info("✅ Índice 'idx_asset_timestamp' criado")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON market_analysis_v2(timestamp DESC)
        """)
        logger.info("✅ Índice 'idx_timestamp' criado")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal 
            ON market_analysis_v2(signal, timestamp DESC) 
            WHERE signal IS NOT NULL
        """)
        logger.info("✅ Índice 'idx_signal' criado")
        
        # Tabela de configurações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        logger.info("✅ Tabela 'system_config' criada/verificada")
        
        # Tabela de logs de execução
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                status TEXT CHECK(status IN ('SUCCESS', 'FAILED', 'RUNNING')),
                message TEXT,
                started_at INTEGER NOT NULL,
                finished_at INTEGER,
                duration_seconds REAL
            )
        """)
        logger.info("✅ Tabela 'execution_log' criada/verificada")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False


def insert_initial_config(conn: sqlite3.Connection) -> bool:
    """Insere configurações iniciais"""
    cursor = conn.cursor()
    
    try:
        configs = [
            ('db_version', '2.0'),
            ('created_at', str(int(datetime.now().timestamp()))),
            ('last_update', str(int(datetime.now().timestamp()))),
            ('default_asset', 'BTCUSDT'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)",
            configs
        )
        
        conn.commit()
        logger.info("✅ Configurações iniciais inseridas")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"❌ Erro ao inserir configurações: {e}")
        return False


def verify_database(conn: sqlite3.Connection) -> bool:
    """Verifica a integridade do banco de dados"""
    cursor = conn.cursor()
    
    try:
        # Verificar tabelas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['market_analysis_v2', 'system_config', 'execution_log']
        missing = set(expected_tables) - set(tables)
        
        if missing:
            logger.warning(f"⚠️ Tabelas faltando: {missing}")
            return False
        
        logger.info(f"✅ Todas as tabelas encontradas: {tables}")
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ Índices encontrados: {indexes}")
        
        # Testar integridade
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result == 'ok':
            logger.info("✅ Integridade do banco verificada: OK")
            return True
        else:
            logger.error(f"❌ Problema de integridade: {result}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return False


def get_database_stats(conn: sqlite3.Connection) -> dict:
    """Retorna estatísticas do banco de dados"""
    cursor = conn.cursor()
    stats = {}
    
    try:
        # Tamanho do arquivo
        stats['db_size_mb'] = DB_PATH.stat().st_size / (1024 * 1024)
        
        # Contagem de registros
        cursor.execute("SELECT COUNT(*) FROM market_analysis_v2")
        stats['total_records'] = cursor.fetchone()[0]
        
        # Registros por asset
        cursor.execute("""
            SELECT asset, COUNT(*) 
            FROM market_analysis_v2 
            GROUP BY asset
        """)
        stats['records_by_asset'] = dict(cursor.fetchall())
        
        # Último registro
        cursor.execute("""
            SELECT MAX(timestamp) 
            FROM market_analysis_v2
        """)
        last_ts = cursor.fetchone()[0]
        if last_ts:
            stats['last_record_time'] = datetime.fromtimestamp(last_ts).isoformat()
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return {}


def optimize_database(conn: sqlite3.Connection) -> bool:
    """Otimiza o banco de dados"""
    cursor = conn.cursor()
    
    try:
        logger.info("🔧 Otimizando banco de dados...")
        
        # Atualizar estatísticas
        cursor.execute("ANALYZE")
        logger.info("✅ Estatísticas atualizadas")
        
        # Vacuum (compactar)
        cursor.execute("VACUUM")
        logger.info("✅ Banco compactado")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"❌ Erro na otimização: {e}")
        return False


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def create_database(verify: bool = True, optimize: bool = False) -> bool:
    """
    Cria e configura o banco de dados completo
    
    Args:
        verify: Se True, verifica a integridade após criação
        optimize: Se True, otimiza o banco após criação
    
    Returns:
        bool: True se sucesso, False caso contrário
    """
    logger.info("=" * 60)
    logger.info("🚀 Maria Helena - Inicializando Banco de Dados")
    logger.info("=" * 60)
    
    # 1. Criar diretório
    if not ensure_directory():
        return False
    
    # 2. Conectar ao banco
    try:
        conn = sqlite3.connect(DB_PATH)
        logger.info(f"📊 Conectado ao banco: {DB_PATH}")
        
        # Habilitar foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Erro ao conectar: {e}")
        return False
    
    # 3. Criar tabelas
    if not create_tables(conn):
        conn.close()
        return False
    
    # 4. Inserir configurações
    if not insert_initial_config(conn):
        conn.close()
        return False
    
    # 5. Verificar integridade
    if verify:
        if not verify_database(conn):
            conn.close()
            return False
    
    # 6. Otimizar
    if optimize:
        if not optimize_database(conn):
            conn.close()
            return False
    
    # 7. Mostrar estatísticas
    stats = get_database_stats(conn)
    logger.info("=" * 60)
    logger.info("📊 ESTATÍSTICAS DO BANCO DE DADOS")
    logger.info("=" * 60)
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    
    # 8. Fechar conexão
    conn.close()
    logger.info("=" * 60)
    logger.info("✅ Banco de dados criado com sucesso!")
    logger.info(f"�� Localização: {DB_PATH}")
    logger.info("=" * 60)
    
    return True


# ==========================================
# PONTO DE ENTRADA
# ==========================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Maria Helena - Database Creator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python create_db.py                    # Criação básica
  python create_db.py --verify           # Com verificação de integridade
  python create_db.py --optimize         # Com otimização
  python create_db.py --verify --optimize # Completo
        """
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verificar integridade após criação'
    )
    
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='Otimizar banco após criação'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose (mais logs)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = create_database(
        verify=args.verify,
        optimize=args.optimize
    )
    
    exit(0 if success else 1)
