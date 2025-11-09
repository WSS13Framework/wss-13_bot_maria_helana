# strategies/mentor_signal_processor.py

from rich.console import Console
from datetime import datetime
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

console = Console()

class MentorSignalProcessor:
    """
    Processa sinais de mentores/grupos, mas SEMPRE valida
    
    REGRA DE OURO:
    - Sinal externo é SUGESTÃO, não ordem
    - Maria Helena decide se executa ou não
    - Aprendizado vem da comparação: expectativa vs realidade
    """
    
    def __init__(self, normalizer, risk_manager, config):
        self.normalizer = normalizer
        self.risk_manager = risk_manager
        self.config = config
        self.mentor_validation_threshold = config.get('mentor_validation_threshold', 0.65)
        
        # Tracking de aprendizado
        self.signals_received = []
        self.signals_followed = []
        self.signals_ignored = []
        
        logger.info("[blue]🎓 Modo Aprendizado: Processador de Sinais ativado[/blue]")
    
    def receive_mentor_signal(self, signal_data):
        """
        Recebe sinal do mentor
        
        signal_data = {
            'source': 'Mentor João',
            'symbol': 'BTC/USDT',
            'action': 'BUY',  # ou 'SELL'
            'reason': 'RSI oversold',
            'confidence': 0.75,  # Confiança do mentor
            'entry_price': 67500,
            'timestamp': datetime.now()
        }
        """
        logger.info(f"\n[blue]📨 Sinal recebido de: {signal_data['source']}[/blue]")
        logger.info(f"   {signal_data['action']} {signal_data['symbol']}")
        logger.info(f"   Razão: {signal_data['reason']}")
        
        # Registra sinal recebido
        signal_data['received_at'] = datetime.now()
        self.signals_received.append(signal_data)
        
        # VALIDA com Maria Helena
        decision = self.validate_signal(signal_data)
        
        return decision
    
    def validate_signal(self, mentor_signal):
        """
        VALIDAÇÃO CRÍTICA - Maria Helena decide
        
        Returns:
            dict: {
                'should_execute': bool,
                'maria_confidence': float,
                'reasons': list,
                'final_signal': dict or None
            }
        """
        logger.info("\n[yellow]🤖 Maria Helena analisando...[/yellow]")
        
        reasons = []
        maria_confidence = 0.0
        
        # 1. PEGA DADOS REAIS DO MERCADO (não confia cegamente)
        # TODO: Implementar chamada real à exchange para dados frescos
        # Por enquanto, placeholder
        try:
            # Aqui você precisaria de uma função para pegar dados atuais,
            # talvez do bot principal ou de um módulo de dados.
            # Por simplicidade, vamos simular.
            current_price = mentor_signal.get('entry_price', 0) # Usa o preço do sinal como "atual" para teste
            if current_price == 0:
                raise ValueError("Preço de entrada do sinal inválido.")
            
            # Simula dados normalizados
            # Em um cenário real, você chamaria self.normalizer.process(ohlcv, ticker)
            normalized = {
                'rsi_norm': self._simulate_rsi_norm(mentor_signal['action']),
                'volume_norm': 0.75, # Simula volume alto
                'price': current_price,
                'trend': 'neutral'
            }
            
        except Exception as e:
            reasons.append(f"❌ Erro pegando dados ou simulando: {e}")
            return self._reject_signal(mentor_signal, reasons)
        
        # 2. NORMALIZA com SEU sistema (já simulado acima)
        
        # 3. COMPARA sinal do mentor com SUA análise
        agreement_score = self._compare_analysis(mentor_signal, normalized)
        
        # 4. VALIDA CONDIÇÕES DE MARIA HELENA
        
        # 4.1: RSI confirma?
        rsi_check = self._check_rsi(normalized, mentor_signal['action'])
        if rsi_check['valid']:
            maria_confidence += 0.30
            reasons.append(f"✅ RSI confirma: {rsi_check['value']:.2f}")
        else:
            reasons.append(f"⚠️  RSI diverge: {rsi_check['value']:.2f}")
        
        # 4.2: Volume suficiente?
        vol_check = self._check_volume(normalized)
        if vol_check['valid']:
            maria_confidence += 0.25
            reasons.append(f"✅ Volume adequado: {vol_check['normalized']:.2f}")
        else:
            reasons.append(f"⚠️  Volume baixo: {vol_check['normalized']:.2f}")
        
        # 4.3: Acordo com análise do mentor?
        if agreement_score > 0.70:
            maria_confidence += 0.25
            reasons.append(f"✅ Análise alinhada: {agreement_score:.2%}")
        else:
            reasons.append(f"⚠️  Análise divergente: {agreement_score:.2%}")
        
        # 4.4: Confiança do mentor é alta?
        mentor_conf = mentor_signal.get('confidence', 0.5)
        if mentor_conf >= 0.70:
            maria_confidence += 0.20
            reasons.append(f"✅ Mentor confiante: {mentor_conf:.2%}")
        else:
            reasons.append(f"⚠️  Mentor incerto: {mentor_conf:.2%}")
        
        # 5. DECISÃO FINAL
        threshold = self.mentor_validation_threshold  # Maria precisa de X% de confiança
        
        if maria_confidence >= threshold:
            logger.info(f"[green]✅ Maria Helena APROVA (confiança: {maria_confidence:.2%})[/green]")
            
            final_signal = {
                'action': mentor_signal['action'],
                'symbol': mentor_signal['symbol'],
                'price': normalized['price'], # Usa o preço que Maria Helena "viu"
                'confidence': maria_confidence,
                'source': f"{mentor_signal['source']} + Maria Helena",
                'reasons': reasons,
                'original_signal': mentor_signal
            }
            
            self.signals_followed.append({
                'mentor_signal': mentor_signal,
                'maria_decision': final_signal,
                'timestamp': datetime.now()
            })
            
            return {
                'should_execute': True,
                'maria_confidence': maria_confidence,
                'reasons': reasons,
                'final_signal': final_signal
            }
        
        else:
            logger.info(f"[red]❌ Maria Helena REJEITA (confiança: {maria_confidence:.2%})[/red]")
            
            self.signals_ignored.append({
                'mentor_signal': mentor_signal,
                'maria_confidence': maria_confidence,
                'reasons': reasons,
                'timestamp': datetime.now()
            })
            
            return {
                'should_execute': False,
                'maria_confidence': maria_confidence,
                'reasons': reasons,
                'final_signal': None
            }
    
    def _simulate_rsi_norm(self, action):
        """Simula um RSI normalizado que tende a confirmar o sinal para testes"""
        if action == 'BUY':
            return 0.28 # Simula oversold
        elif action == 'SELL':
            return 0.72 # Simula overbought
        return 0.5
        
    def _check_rsi(self, normalized_data, action):
        """Verifica se RSI confirma a ação sugerida"""
        rsi_norm = normalized_data.get('rsi_norm', 0.5)
        rsi_value = rsi_norm * 100  # Converte de volta para 0-100
        
        if action == 'BUY':
            # Para compra, queremos RSI baixo (oversold)
            valid = rsi_value < self.config.get('rsi_oversold', 30) + 5 # +5 de margem para simulação
        else:  # SELL
            # Para venda, queremos RSI alto (overbought)
            valid = rsi_value > self.config.get('rsi_overbought', 70) - 5 # -5 de margem para simulação
        
        return {'valid': valid, 'value': rsi_value, 'normalized': rsi_norm}
    
    def _check_volume(self, normalized_data):
        """Verifica se volume é adequado"""
        vol_norm = normalized_data.get('volume_norm', 0.5)
        
        # Volume acima de um threshold é bom sinal
        valid = vol_norm > self.config.get('volume_threshold', 0.60)
        
        return {'valid': valid, 'normalized': vol_norm}
    
    def _compare_analysis(self, mentor_signal, maria_normalized):
        """
        Compara análise do mentor com análise de Maria
        
        Returns:
            float: Score de concordância (0-1)
        """
        agreement_points = 0
        total_checks = 0
        
        # Verifica se ambos veem mesma direção
        mentor_action = mentor_signal['action']
        rsi_norm = maria_normalized.get('rsi_norm', 0.5)
        
        # Se o mentor diz BUY e Maria vê RSI baixo
        if mentor_action == 'BUY' and rsi_norm < 0.40:
            agreement_points += 1
        # Se o mentor diz SELL e Maria vê RSI alto
        elif mentor_action == 'SELL' and rsi_norm > 0.60:
            agreement_points += 1
        
        total_checks += 1
        
        # Adicione mais comparações conforme aprender
        
        return agreement_points / total_checks if total_checks > 0 else 0
    
    def _reject_signal(self, signal, reasons):
        """Helper para rejeitar sinal"""
        logger.info(f"[red]❌ Sinal REJEITADO[/red]")
        for reason in reasons:
            logger.info(f"   {reason}")
        
        return {
            'should_execute': False,
            'maria_confidence': 0.0,
            'reasons': reasons,
            'final_signal': None
        }
    
    def get_learning_stats(self):
        """Estatísticas de aprendizado"""
        total = len(self.signals_received)
        followed = len(self.signals_followed)
        ignored = len(self.signals_ignored)
        
        logger.info("\n[cyan]📊 ESTATÍSTICAS DE APRENDIZADO[/cyan]")
        logger.info(f"   Sinais recebidos: {total}")
        logger.info(f"   Sinais seguidos: {followed} ({followed/total*100:.1f}%) " if total > 0 else "   Sinais seguidos: 0 (0.0%)")
        logger.info(f"   Sinais ignorados: {ignored} ({ignored/total*100:.1f}%) " if total > 0 else "   Sinais ignorados: 0 (0.0%)")
        
        return {
            'total': total,
            'followed': followed,
            'ignored': ignored,
            'follow_rate': followed / total if total > 0 else 0
        }
