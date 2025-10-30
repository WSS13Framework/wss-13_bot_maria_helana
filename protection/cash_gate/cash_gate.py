# protection/cash_gate/cash_gate.py

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

# Importar CONFIG para acessar max_position_size
from config import CONFIG
import logging

# Configuração de logging para o CashGate
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATE_PATH = Path("cash_gate_state.json")


class CashGate:
    def __init__(self, initial_capital: float = 0.0) -> None:
        self._lock = threading.Lock()
        self.current_capital: float = float(initial_capital)
        # _reserved: soma dos valores reservados para ordens pendentes
        self._reserved: float = 0.0
        
        # --- REGRA DE NEGÓCIO INTRODUZIDA NO CASHGATE ---
        # Pega do CONFIG, default 3% se não estiver definido
        self.max_position_size_pct = CONFIG.get('max_position_size', 0.03) 
        # --- FIM REGRA DE NEGÓCIO ---

        self._load_state()
        logger.info(f"CashGate inicializado com capital: {self.current_capital:.2f}, reservado: {self._reserved:.2f}. Max position size: {self.max_position_size_pct:.2%}")


    def _load_state(self) -> None:
        """Carrega o estado do CashGate de um arquivo JSON."""
        try:
            if STATE_PATH.exists():
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                self.current_capital = float(data.get("current_capital", self.current_capital))
                self._reserved = float(data.get("reserved", self._reserved))
                logger.info(f"CashGate estado carregado: capital={self.current_capital:.2f}, reservado={self._reserved:.2f}")
        except Exception as e:
            logger.error(f"Falha ao carregar estado do CashGate de '{STATE_PATH}': {e}. Mantendo estado em memória.")
            # falha silenciosa — mantém estado em memória
            pass

    def _persist(self) -> None:
        """Persiste o estado atual do CashGate em um arquivo JSON."""
        try:
            STATE_PATH.write_text(
                json.dumps({"current_capital": self.current_capital, "reserved": self._reserved}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Falha ao persistir estado do CashGate em '{STATE_PATH}': {e}")
            pass

    def get_available(self) -> float:
        """Retorna o capital disponível para novas reservas (capital total - capital reservado)."""
        with self._lock:
            return max(0.0, self.current_capital - self._reserved)

    def can_reserve(self, amount: float) -> (bool, str):
        """
        Verifica se `amount` pode ser reservado, aplicando regras de negócio.
        Retorna (True, "Razão") se aprovado, (False, "Razão") se rejeitado.
        """
        if amount <= 0:
            return False, "Valor a reservar deve ser positivo."
        
        with self._lock:
            # 1. Verificar disponibilidade de fundos
            if amount > self.get_available():
                return False, f"Capital insuficiente. Disponível: {self.get_available():.2f}, Requerido: {amount:.2f}."
            
            # 2. Verificar regra de negócio: Tamanho máximo por posição
            # O capital total atual é a base para calcular o tamanho máximo da posição.
            max_single_position_value = self.current_capital * self.max_position_size_pct
            if amount > max_single_position_value:
                return False, f"Alocação de {amount:.2f} excede o limite máximo por posição ({max_single_position_value:.2f})."
            
            return True, "Reserva aprovada pelo CashGate."

    def reserve(self, amount: float) -> bool:
        """
        Tenta reservar `amount` do capital disponível.
        Retorna True se reservado, False se insuficiente ou se regras de negócio não forem atendidas.
        """
        approved, reason = self.can_reserve(amount)
        if not approved:
            logger.warning(f"Reserva de {amount:.2f} REJEITADA pelo CashGate: {reason}")
            return False
        
        with self._lock:
            self._reserved += amount
            self._persist()
            logger.info(f"Reserva de {amount:.2f} APROVADA. Total reservado: {self._reserved:.2f}.")
            return True

    def release(self, amount: float) -> None:
        """Libera uma reserva (rollback)."""
        if amount <= 0:
            return
        with self._lock:
            self._reserved = max(0.0, self._reserved - amount)
            self._persist()
            logger.info(f"Reserva de {amount:.2f} LIBERADA. Total reservado: {self._reserved:.2f}.")


    def commit(self, amount: float) -> None:
        """
        Confirma gasto: remove da reserva e do capital (quando ordem executa).
        Use commit depois que a execução foi confirmada.
        """
        if amount <= 0:
            return
        with self._lock:
            # remove da reserva e do capital real
            self._reserved = max(0.0, self._reserved - amount)
            self.current_capital = max(0.0, self.current_capital - amount)
            self._persist()
            logger.info(f"Gasto de {amount:.2f} CONFIRMADO. Capital atual: {self.current_capital:.2f}, reservado: {self._reserved:.2f}.")


    def deposit(self, amount: float) -> None:
        """Aumenta capital (ex.: após venda ou ajuste manual)."""
        if amount <= 0:
            return
        with self._lock:
            self.current_capital += amount
            self._persist()
            logger.info(f"Depósito de {amount:.2f} realizado. Capital atual: {self.current_capital:.2f}.")

    def get_status(self) -> dict:
        """Retorna o status atual do CashGate."""
        with self._lock:
            return {
                "current_capital": self.current_capital,
                "reserved_capital": self._reserved,
                "available_capital": self.get_available(),
                "max_position_size_pct": self.max_position_size_pct
            }
