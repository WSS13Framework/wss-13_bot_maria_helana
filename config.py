#!/usr/bin/env python3
"""
⚙️ Configuração - Maria Helena Trading Bot
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CONFIG: Dict[str, Any] = {
    # ======================================================================= #
    #                                BOT INFO                                 #
    # ======================================================================= #
    'BOT_NAME': 'Maria Helena',
    'BOT_VERSION': '0.3.0 - Estratégia RSI Aprimorada',

    # ======================================================================= #
    #                                 EXCHANGE                                #
    # ======================================================================= #
    'EXCHANGE': 'binance',
    'SYMBOL': 'BTC/USDT',
    'TIMEFRAME': '15m',
    'TESTNET': False,
    'OPTIONS': {
        'defaultType': 'spot'
    },
    'API_KEY': os.getenv('BINANCE_API_KEY', ''),
    'SECRET_KEY': os.getenv('BINANCE_SECRET_KEY', ''),

    # ======================================================================= #
    #                                  CAPITAL                                #
    # ======================================================================= #
    'INITIAL_CAPITAL': 1000.0,
    'MAX_POSITION_SIZE': 0.03,

    # ======================================================================= #
    #                             BOT BEHAVIOR                                #
    # ======================================================================= #
    'MENTOR_MODE': False,
    'LIVE_MODE': False,
    'CHECK_INTERVAL': 60,

    # ======================================================================= #
    #                         ESTRATÉGIA - RSI & VOLUME                       #
    # ======================================================================= #
    'RSI_PERIOD': 14,
    'RSI_OVERSOLD': 0.40,
    'RSI_OVERBOUGHT': 0.70,
    'VOLUME_THRESHOLD': 0.60,
    'LOOKBACK_PERIOD': 100,

    # ======================================================================= #
    #                    ESTRATÉGIA - THRESHOLDS POR TENDÊNCIA                #
    # ======================================================================= #
    'RSI_SELL_UPTREND': 0.75,
    'RSI_SELL_NEUTRAL': 0.70,
    'RSI_SELL_DOWNTREND': 0.65,

    # ======================================================================= #
    #                            RISK MANAGEMENT                              #
    # ======================================================================= #
    'MAX_DAILY_LOSS': 0.05,
    'MAX_CONSECUTIVE_LOSSES': 3,
    'STOP_LOSS': 0.02,
    'TAKE_PROFIT': 0.05,
    'STOP_LOSS_PCT': 0.02,
    'TAKE_PROFIT_PCT': 0.05,
    'MAX_TOTAL_EXPOSURE': 0.15,
    'MAX_TRADES_PER_DAY': 5,
    'MIN_TIME_BETWEEN_TRADES': 300,

    # ======================================================================= #
    #                                TELEGRAM                                 #
    # ======================================================================= #
    'TELEGRAM_ENABLED': False,
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),

    # ======================================================================= #
    #                                 LOGGING                                 #
    # ======================================================================= #
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'maria_helena_bot.log',
    'LOG_TO_CONSOLE': True,
}

# ======================================================================= #
#                             VALIDAÇÃO DA CONFIGURAÇÃO                   #
# ======================================================================= #

def validate_config(config: Dict[str, Any]) -> None:
    """Valida a configuração do bot"""
    required_keys = [
        'EXCHANGE', 'SYMBOL', 'TIMEFRAME', 'TESTNET', 'OPTIONS',
        'INITIAL_CAPITAL', 'MAX_POSITION_SIZE', 'MENTOR_MODE', 'LIVE_MODE',
        'CHECK_INTERVAL', 'RSI_PERIOD', 'RSI_OVERSOLD', 'RSI_OVERBOUGHT',
        'VOLUME_THRESHOLD', 'LOOKBACK_PERIOD', 'RSI_SELL_UPTREND',
        'RSI_SELL_NEUTRAL', 'RSI_SELL_DOWNTREND', 'MAX_DAILY_LOSS',
        'MAX_CONSECUTIVE_LOSSES', 'STOP_LOSS', 'TAKE_PROFIT',
        'TELEGRAM_ENABLED', 'LOG_LEVEL', 'LOG_FILE', 'LOG_TO_CONSOLE'
    ]

    for key in required_keys:
        if key not in config:
            logger.critical(f"Erro: Chave '{key}' faltando no CONFIG.")
            raise KeyError(f"Chave '{key}' ausente.")

    if not isinstance(config['INITIAL_CAPITAL'], (int, float)) or config['INITIAL_CAPITAL'] <= 0:
        logger.error("INITIAL_CAPITAL deve ser positivo.")
        config['INITIAL_CAPITAL'] = 1000.0
    
    if not (0 < config['MAX_POSITION_SIZE'] <= 1):
        logger.error("MAX_POSITION_SIZE deve estar entre 0 e 1.")
        config['MAX_POSITION_SIZE'] = 0.03

    if not config['TESTNET'] and (not config['API_KEY'] or not config['SECRET_KEY']):
        logger.warning("Produção ativada sem API_KEY/SECRET_KEY!")

    logger.info("Configuração validada com sucesso.")

try:
    validate_config(CONFIG)
except KeyError as e:
    logger.critical(f"Falha na validação: {e}")
    raise
