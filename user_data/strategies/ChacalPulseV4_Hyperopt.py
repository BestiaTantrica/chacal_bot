# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timezone
from typing import Optional, Union
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

class ChacalPulseV4_Hyperopt(IStrategy):
    """
    ESTRATEGIA CHACAL V4 (HYPEROPT) - REGIMEN ADAPTATIVO
    """
    
    # ESTRATEGIA CHACAL V4 (HYPEROPT) - REGIMEN ADAPTATIVO
    # Enfoque: Momentum de alta resolución durante aperturas de mercados globales.
    # MODO: LONG & SHORT (Futures 5x)
    
    INTERFACE_VERSION = 3
    can_short: bool = True

    # --- PARÁMETROS HYPEROPTABLES POR RÉGIMEN ---
    
    # 1. Régimen BULL (Tendencia Alcista)
    # Target: Dejar correr ganancias
    bull_roi_0 = DecimalParameter(0.02, 0.15, default=0.023, space="sell", optimize=True)
    bull_stoploss = DecimalParameter(-0.15, -0.05, default=-0.076, space="sell", optimize=True)
    
    # 2. Régimen BEAR (Tendencia Bajista - Defensa)
    # Target: Salir rápido si falla el rebote
    bear_roi_0 = DecimalParameter(0.01, 0.05, default=0.048, space="sell", optimize=True)
    bear_stoploss = DecimalParameter(-0.06, -0.02, default=-0.036, space="sell", optimize=True)
    
    # 3. Régimen SIDEWAYS (Lateral - Scalping)
    # Target: Scalping agresivo
    sideways_roi_0 = DecimalParameter(0.005, 0.025, default=0.025, space="sell", optimize=True)
    sideways_stoploss = DecimalParameter(-0.04, -0.01, default=-0.017, space="sell", optimize=True)

    # Stoploss de Seguridad (El real es dinámico por custom_stoploss)
    stoploss = -0.231

    # Timeframe
    timeframe = '5m'
    
    # --- VALORES OFICIALES FASE 2 (GRABADOS A FUEGO) ---
    v_factors_map = {
        "BTC/USDT:USDT": 4.660,
        "ETH/USDT:USDT": 5.769,
        "SOL/USDT:USDT": 5.386,
        "BNB/USDT:USDT": 3.378,
        "XRP/USDT:USDT": 5.133,
        "ADA/USDT:USDT": 3.408,
        "DOGE/USDT:USDT": 5.795,
        "AVAX/USDT:USDT": 5.692,
        "LINK/USDT:USDT": 5.671,
        "DOT/USDT:USDT": 5.051,
        "SUI/USDT:USDT": 5.508,
        "NEAR/USDT:USDT": 2.772
    }

    # Parámetros Hyperoptables (Solo como referencia, el mapa manda)
    v_factor = DecimalParameter(1.5, 6.0, default=4.319, space="buy", optimize=True)
    pulse_change = DecimalParameter(0.0005, 0.005, default=0.004, space="buy", optimize=True)

    def get_v_factor(self, pair: str) -> float:
        """Retorna el v_factor oficial o un valor defensivo alto."""
        return self.v_factors_map.get(pair, 6.0)


    # --- LEVERAGE (FUTURES REALES) ---
    def leverage(self, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Indicadores Básicos
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']

        # Ventanas Horarias (Hunter)
        dataframe['date_utc'] = pd.to_datetime(dataframe['date'], utc=True)
        dataframe['hour'] = dataframe['date_utc'].dt.hour
        dataframe['minute'] = dataframe['date_utc'].dt.minute
        
        # Ventana 1: 08:00 - 10:00 UTC (Londres)
        # Ventana 2: 13:30 - 17:30 UTC (NY)
        dataframe['is_pulse_window'] = 0
        dataframe.loc[
            ((dataframe['hour'] >= 8) & (dataframe['hour'] < 10)) | 
            ((dataframe['hour'] == 13) & (dataframe['minute'] >= 30)) |
            ((dataframe['hour'] >= 14) & (dataframe['hour'] < 17)) |
            ((dataframe['hour'] == 17) & (dataframe['minute'] <= 30)),
            'is_pulse_window'
        ] = 1

        # Todo es Modo Hunter: Solo en ventana.
        dataframe['gate_open'] = 0
        dataframe.loc[dataframe['is_pulse_window'] == 1, 'gate_open'] = 1

        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']
        
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        """
        Stoploss dinámico basado en régimen de mercado (Bull/Bear/Lateral).
        Usa parámetros optimizados por Hyperopt.
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 1:
                return self.stoploss  # Fallback al stoploss estático
            
            last_candle = dataframe.iloc[-1].squeeze()
            adx = last_candle.get('adx', 0)
            rsi = last_candle.get('rsi', 50)
            
            # BULL: Mercado alcista fuerte (ADX > 25 y RSI > 55)
            if adx > 25 and rsi > 55:
                return self.bull_stoploss.value
            
            # BEAR: Mercado bajista fuerte (ADX > 25 y RSI < 45)
            elif adx > 25 and rsi < 45:
                return self.bear_stoploss.value
            
            # LATERAL: Sin tendencia clara (ADX < 25)
            else:
                return self.sideways_stoploss.value
        except Exception as e:
            # Si falla la detección, usar stoploss estático de seguridad
            return self.stoploss

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Salida dinámica basada en régimen de mercado.
        Usa ROI específico para cada tipo de mercado.
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 1:
                return None
            
            last_candle = dataframe.iloc[-1].squeeze()
            adx = last_candle.get('adx', 0)
            rsi = last_candle.get('rsi', 50)
            
            # Determinar ROI objetivo según régimen
            if adx > 25 and rsi > 55:
                # BULL: Buscar ganancias mayores
                roi_target = self.bull_roi_0.value
                reason = "bull_roi"
            elif adx > 25 and rsi < 45:
                # BEAR: Tomar ganancias rápido (modo defensivo)
                roi_target = self.bear_roi_0.value
                reason = "bear_roi"
            else:
                # LATERAL: Scalping (ganancias pequeñas pero frecuentes)
                roi_target = self.sideways_roi_0.value
                reason = "sideways_roi"
            
            # Salir si alcanzamos el objetivo de ROI para este régimen
            if current_profit >= roi_target:
                return reason
            
            return None
        except Exception as e:
            return None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        
        # LONG: Ventana + Vol Spike + Precio Up
        pulse_long = (
            (dataframe['gate_open'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.get_v_factor(metadata['pair']))) &
            (dataframe['price_change'] > self.pulse_change.value) &
            (dataframe['rsi'] < 80)
        )
        
        dataframe.loc[pulse_long, 'enter_long'] = 1
        dataframe.loc[pulse_long, 'enter_tag'] = 'PULSE_LONG'

        return dataframe

    def populate_entry_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_short'] = 0
        
        # SHORT: Ventana + Vol Spike + Precio Down
        pulse_short = (
            (dataframe['gate_open'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.get_v_factor(metadata['pair']))) &
            (dataframe['price_change'] < -self.pulse_change.value) &
            (dataframe['rsi'] > 20)
        )
        
        dataframe.loc[pulse_short, 'enter_short'] = 1
        dataframe.loc[pulse_short, 'enter_tag'] = 'PULSE_SHORT'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_exit_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
