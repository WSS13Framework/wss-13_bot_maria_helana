#!/usr/bin/env python3
"""
Estratégia de trading baseada em um modelo de Machine Learning (LSTM) treinado.
"""

import pickle
from pathlib import Path
import sqlite3
import numpy as np
from tensorflow.keras.models import load_model

class MLStrategy:
    """
    Carrega um modelo Keras (LSTM) e um scaler Scikit-learn para gerar sinais de trading.
    """
    def __init__(self, model_path: Path, scaler_path: Path, db_path: Path):
        """
        Inicializa a estratégia carregando o modelo e o scaler.

        Args:
            model_path (Path): Caminho para o arquivo do modelo (.h5).
            scaler_path (Path): Caminho para o arquivo do scaler (.pkl).
            db_path (Path): Caminho para o banco de dados de sinais.
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.db_path = db_path
        self.model = None
        self.scaler = None
        self.timesteps = 60  # IMPORTANTE: Assumindo 60 timesteps. Ajustar se necessário.
        self.num_features = 5 # IMPORTANTE: Assumindo 5 features. Ajustar se necessário.

        self._load_artifacts()

    def _load_artifacts(self):
        """Carrega o modelo e o scaler da memória."""
        try:
            print(f"🧠 Carregando modelo de: {self.model_path}")
            self.model = load_model(self.model_path)
            
            print(f"🧠 Carregando scaler de: {self.scaler_path}")
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            print("✅ Cérebro de IA carregado com sucesso.")

        except Exception as e:
            print(f"❌ ERRO CRÍTICO ao carregar artefatos de IA: {e}")
            raise

    def _fetch_latest_data(self, asset: str):
        """Busca os últimos 'timesteps' dados do banco de dados para um ativo."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ATENÇÃO: As colunas aqui precisam ser as mesmas usadas para treinar o modelo!
            # Exemplo: rsi, price, volume, macd, sma
            query = f"""
                SELECT rsi, price, volume, macd, sma 
                FROM market_analysis_v2
                WHERE asset = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            cursor.execute(query, (asset, self.timesteps))
            data = cursor.fetchall()
            conn.close()
            
            if len(data) < self.timesteps:
                print(f"⚠️ Dados insuficientes no DB para {asset}. Encontrados: {len(data)}/{self.timesteps}")
                return None
            
            # Inverter para ordem cronológica correta (mais antigo para mais novo)
            return np.array(data)[::-1]

        except Exception as e:
            print(f"❌ Erro ao buscar dados do DB para a IA: {e}")
            return None

    def analyze(self, asset: str):
        """
        Executa a análise completa usando o modelo de ML.
        """
        # 1. Buscar dados do DB
        latest_data = self._fetch_latest_data(asset)
        if latest_data is None:
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'Dados insuficientes'}

        # 2. Normalizar os dados com o scaler carregado
        scaled_data = self.scaler.transform(latest_data)
        
        # 3. Preparar os dados para o formato do LSTM (samples, timesteps, features)
        reshaped_data = np.reshape(scaled_data, (1, self.timesteps, self.num_features))
        
        # 4. Fazer a previsão com o modelo
        prediction = self.model.predict(reshaped_data)
        
        # 5. Interpretar a previsão
        # Exemplo: prediction[0] pode ser [prob_venda, prob_compra, prob_hold]
        signal_index = np.argmax(prediction[0])
        confidence = prediction[0][signal_index]
        
        action = 'HOLD'
        if signal_index == 0: # Assumindo que 0 é Venda
            action = 'SELL'
        elif signal_index == 1: # Assumindo que 1 é Compra
            action = 'BUY'
            
        print(f"🤖 Previsão da IA para {asset}: {action} com confiança de {confidence:.2f}")
        
        return {'action': action, 'confidence': float(confidence)}

