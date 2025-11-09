import time
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path
import os

class TelegramNotifier:
    """
    Sistema de notificações para Telegram com:
    - Envio para múltiplos chats
    - Rate limiting (1 msg/segundo)
    - Suporte a MarkdownV2
    - Tratamento de erros robusto
    """
    
    def __init__(self, timeout: int = 15):
        self._load_credentials()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'WSS+13 Trading Bot'
        })
        self.timeout = timeout
        self.last_message_time = datetime.min
        self.chat_ids = [
            "1617889564",  # Seu chat_id
            "7436181680"   # Chat_id do parceiro
        ]

    def _load_credentials(self):
        """Carrega e valida as credenciais do Telegram"""
        env_path = Path(__file__).parent.parent.parent / '.env'
        if not env_path.exists():
            raise FileNotFoundError("Arquivo .env não encontrado")
        
        load_dotenv(env_path)
        self.token = os.getenv('TELEGRAM_TOKEN')
        
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN não configurado no .env")

    def _rate_limit_check(self):
        """Controla o intervalo entre mensagens"""
        elapsed = (datetime.now() - self.last_message_time).total_seconds()
        if elapsed < 1:
            time.sleep(1 - elapsed)

    def _send_single_message(self, chat_id: str, payload: Dict[str, Any]) -> bool:
        """Envia mensagem para um único chat"""
        try:
            response = self.session.post(
                f"{self.base_url}/sendMessage",
                json={**payload, "chat_id": chat_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar para {chat_id}: {str(e)}")
            return False

    def send_text(self, message: str, parse_mode: Optional[str] = None) -> bool:
        """
        Envia mensagem para todos os chats configurados
        
        Args:
            message: Texto da mensagem
            parse_mode: None ou "MarkdownV2"
        """
        if not message or not isinstance(message, str):
            raise ValueError("Mensagem inválida")
            
        payload = {
            "text": self._escape_markdown(message) if parse_mode == "MarkdownV2" else message
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        self._rate_limit_check()
        results = [self._send_single_message(chat_id, payload) for chat_id in self.chat_ids]
        return all(results)

    def send_trade_alert(self, trade_data: Dict[str, Any]) -> bool:
        """
        Envia alerta de trade formatado para todos os chats
        """
        try:
            emoji = "🟢" if trade_data.get('action', '').upper() == "BUY" else "🔴"
            msg = (
                f"{emoji} *ALERTA*: {trade_data['pair']}\n"
                f"• Ação: {trade_data['action'].upper()}\n"
                f"• Preço: ${trade_data['price']:,.2f}\n"
                f"• Volume: {trade_data['volume']}\n"
                f"• Motivo: {trade_data.get('reason', 'N/A')}"
            )
            return self.send_text(msg, parse_mode="MarkdownV2")
        except KeyError as e:
            logging.error(f"Dados incompletos: {e}")
            return False

    @staticmethod
    def _escape_markdown(text: str) -> str:
        escape_chars = '_*[]()~`>#+-=|{}.!'
        return ''.join(f'\{char}' if char in escape_chars else char for char in text)

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('notifier.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger(__name__)
    
    try:
        notifier = TelegramNotifier()
        
        # Teste de mensagem simples
        notifier.send_text("🔔 Bot iniciado com sucesso!")
        
        # Teste de trade alert
        trade_data = {
            "pair": "BTC/USDT",
            "action": "buy",
            "price": 51234.56,
            "volume": 0.05,
            "reason": "Breakout"
        }
        notifier.send_trade_alert(trade_data)
        
        logger.info("✅ Testes concluídos")
    except Exception as e:
        logger.error(f"Erro: {str(e)}")