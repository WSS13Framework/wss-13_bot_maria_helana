from config import CONFIG
from rich.console import Console

console = Console()

try:
    console.print("[green]✅ Importação de config.py bem-sucedida![/green]")
    console.print(f"   Nome do Bot: [cyan]{CONFIG['bot_name']}[/cyan]")
    console.print(f"   Capital Inicial: [yellow]${CONFIG['initial_capital']}[/yellow]")
except Exception as e:
    console.print(f"[red]❌ Erro ao importar config.py: {e}[/red]")
