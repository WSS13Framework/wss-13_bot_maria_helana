"""
⚙️ Configuração - Maria Helena Trading Bot
Todos os parâmetros em um lugar só
"""

CONFIG = {
    # === BOT INFO ===
    'bot_name': 'Maria Helena',
    'bot_version': '0.2.0',
    
    # === EXCHANGE ===
    'exchange': 'binance', # Mantém 'binance' para o CCXT identificar a classe
    'symbol': 'BTC/USDT',
    'timeframe': '1h',
    
    # === CONFIGURAÇÕES PARA BINANCE REAL (MODIFICADO!) ===
    # Ative 'testnet': True para usar o ambiente de testnet
    'testnet': False, 
    # Remova as linhas 'urls' e 'options' específicas da Testnet
    # 'urls': {
    #     'api': 'https://testnet.binance.vision/api'
    # },
    'options': {
        'defaultType': 'spot' # Tipo de mercado (spot, future, etc.)
    },
    # ==================================================
    
    # === CAPITAL (3% por trade como você pediu!) ===
    'initial_capital': 1000,
    'max_position_size': 0.03,  # 3% do capital por trade
    
    # === GESTÃO DE RISCO (3 camadas de proteção) ===
    'max_daily_loss': 0.05,        # 5% perda diária = para tudo
    'max_capital_loss': 0.20,      # 20% perda total = KILL SWITCH
    'stop_loss_pct': 0.02,         # 2% stop loss por trade
    'max_total_exposure': 0.15,    # Máximo 15% exposto (5 trades de 3%)
    
    # === LIMITES OPERACIONAIS ===
    'max_trades_per_day': 5,
    'min_time_between_trades': 300,  # 5 minutos entre trades
    'max_consecutive_losses': 5,      # 5 perdas seguidas = pausa
    
    # === ESTRATÉGIA - RSI + VOLUME ===
    'rsi_period': 14,
    'rsi_oversold': 30,      # Compra quando RSI < 30
    'rsi_overbought': 70,    # Vende quando RSI > 70
    'volume_threshold': 0.70, # Volume precisa estar > 70% normalizado
    
    # === NORMALIZAÇÃO ===
    'lookback_period': 100,   # Janela de 100 períodos para normalizar
    
    # === BACKTEST ===
    'backtest_days': 90,      # Testa em 90 dias de dados
    
    # === MODO MENTORIA ===
    'mentor_mode': False,      # Ativa quando quiser aprender com sinais externos
    'mentor_validation_threshold': 0.65,
}

# Atalhos úteis
def get_position_size_in_currency(capital=None):
    """Retorna tamanho de posição em dinheiro"""
    if capital is None:
        capital = CONFIG['initial_capital']
    return capital * CONFIG['max_position_size']

def get_max_loss_per_trade(capital=None):
    """
    Retorna a perda máxima por trade em unidades da moeda base.

    Args:
        capital (float | int | None): Capital total usado para calcular o tamanho da posição.
            Se None, usa CONFIG['initial_capital'].

    Returns:
        float: Perda máxima aceitável por trade (valor em moeda), calculada como
            get_position_size_in_currency(capital) * CONFIG['stop_loss_pct'].

    Raises:
        KeyError: Se CONFIG não contiver as chaves necessárias ('initial_capital' ou 'stop_loss_pct').
        TypeError: Se o valor de capital não for numérico.
        Propaga exceções levantadas por get_position_size_in_currency.

    Examples:
        >>> get_max_loss_per_trade(10000)
        50.0  # Exemplo ilustrativo, depende de get_position_size_in_currency e CONFIG
    """
    """Retorna perda máxima por trade"""
    if capital is None:
        capital = CONFIG['initial_capital']
    position_size = get_position_size_in_currency(capital)
    return position_size * CONFIG['stop_loss_pct']

# Mostra info quando importado
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("\n[bold cyan]⚙️  Configuração - Maria Helena[/bold cyan]\n")
    
    table = Table(title="Parâmetros Principais")
    table.add_column("Parâmetro", style="cyan")
    table.add_column("Valor", style="green")
    table.add_column("Descrição", style="white")
    
    table.add_row(
        "Capital Inicial",
        f"${CONFIG['initial_capital']:,.2f}",
        "Dinheiro para começar"
    )
    
    table.add_row(
        "Tamanho Posição",
        f"{CONFIG['max_position_size']:.1%}",
        f"${get_position_size_in_currency():,.2f} por trade"
    )
    
    table.add_row(
        "Stop Loss",
        f"{CONFIG['stop_loss_pct']:.1%}",
        f"Max ${get_max_loss_per_trade():.2f} por trade"
    )
    
    table.add_row(
        "Perda Diária Máx",
        f"{CONFIG['max_daily_loss']:.1%}",
        f"${CONFIG['initial_capital'] * CONFIG['max_daily_loss']:.2f} = PARA TUDO"
    )
    
    table.add_row(
        "Exposição Máx",
        f"{CONFIG['max_total_exposure']:.1%}",
        "Máximo exposto simultaneamente"
    )
    
    console.print(table)
    
    console.print("\n[yellow]💡 Maria é cautelosa: 3% por trade, proteções em 3 camadas[/yellow]\n")