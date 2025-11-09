with open('bot.py', 'r') as f:
    content = f.read()

# Procura onde mostra o status_message e adiciona o processamento logo após
import re

# Padrão: após o else que mostra erro de dados
pattern = r"(console\.print\(f\"\[red\]\{now\} \| ❌ Não foi possível obter dados do mercado\. Pulando iteração\.\[/red\]\"\))"

replacement = r"""\1
                
                # 📊 PROCESSA DADOS SE TIVER TICKER E OHLCV
                if ticker and ohlcv:
                    console.print("[dim]   🔄 Processando dados...[/dim]")
                    
                    # Normaliza dados
                    normalized_data = self.normalizer.process(ohlcv, ticker)
                    
                    # Avalia estratégia
                    signal = self.rsi_volume_strategy.evaluate(normalized_data)
                    
                    if signal:
                        console.print(f"[bold magenta]💡 Sinal: {signal['action']} @ ${signal['price']:.2f} (Confiança: {signal['confidence']:.2%})[/bold magenta]")
                        # TODO: Aqui entraria execução de trade real
"""

content = re.sub(pattern, replacement, content)

with open('bot.py', 'w') as f:
    f.write(content)

print("✅ Processamento de estratégia adicionado!")
