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
    bull_roi_0 = DecimalParameter(0.01, 0.20, default=0.05, space="sell", optimize=True)
    bull_stoploss = DecimalParameter(-0.15, -0.04, default=-0.08, space="sell", optimize=True)
    
    # 2. Régimen BEAR (Tendencia Bajista)
    bear_roi_0 = DecimalParameter(0.005, 0.10, default=0.02, space="sell", optimize=True)
    bear_stoploss = DecimalParameter(-0.10, -0.02, default=-0.05, space="sell", optimize=True)
    
    # 3. Régimen SIDEWAYS (Lateral)
    sideways_roi_0 = DecimalParameter(0.002, 0.05, default=0.01, space="sell", optimize=True)
    sideways_stoploss = DecimalParameter(-0.05, -0.01, default=-0.02, space="sell", optimize=True)

    # --- PARÁMETROS DINÁMICOS (COMPRA) ---
    # Mutabilidad fina: El multiplicador puede reducir el v_factor a la mitad en lateral o aumentarlo en tendencia.
    v_factor_mult_sideways = DecimalParameter(0.3, 1.0, default=0.6, space="buy", optimize=True)
    v_factor_mult_trend = DecimalParameter(0.7, 1.5, default=1.1, space="buy", optimize=True)

    # --- PARÁMETROS DE TIEMPO (SALIDA MUTABLE) ---
    trade_duration_max = IntParameter(30, 600, default=240, space="sell", optimize=True)

    # Stoploss de Seguridad (El real es dinámico por custom_stoploss)
    stoploss = -0.231

    # Timeframe
    timeframe = '5m'
    
    # --- TABLA MAESTRA ADN HYPEROPT (FASE 2 - FEBRERO 2026) ---
    # Cada moneda opera con el set exacto que dio ganancia en backtest.
    hyperopt_dna = {
        "BTC/USDT:USDT": {
            "v_factor": 4.660, "pulse_change": 0.004,
            "bull_roi": 0.027, "bull_sl": -0.124,
            "bear_roi": 0.022, "bear_sl": -0.031,
            "side_roi": 0.014, "side_sl": -0.015
        },
        "ETH/USDT:USDT": {
            "v_factor": 5.769, "pulse_change": 0.004,
            "bull_roi": 0.024, "bull_sl": -0.138,
            "bear_roi": 0.018, "bear_sl": -0.031,
            "side_roi": 0.007, "side_sl": -0.011
        },
        "SOL/USDT:USDT": {
            "v_factor": 5.386, "pulse_change": 0.001,
            "bull_roi": 0.148, "bull_sl": -0.05,
            "bear_roi": 0.042, "bear_sl": -0.04,
            "side_roi": 0.019, "side_sl": -0.013
        },
        "BNB/USDT:USDT": {
            "v_factor": 3.378, "pulse_change": 0.003,
            "bull_roi": 0.027, "bull_sl": -0.117,
            "bear_roi": 0.011, "bear_sl": -0.048,
            "side_roi": 0.005, "side_sl": -0.011
        },
        "XRP/USDT:USDT": {
            "v_factor": 5.133, "pulse_change": 0.004,
            "bull_roi": 0.053, "bull_sl": -0.12,
            "bear_roi": 0.042, "bear_sl": -0.054,
            "side_roi": 0.023, "side_sl": -0.032
        },
        "ADA/USDT:USDT": {
            "v_factor": 3.408, "pulse_change": 0.005,
            "bull_roi": 0.196, "bull_sl": -0.042,
            "bear_roi": 0.042, "bear_sl": -0.022,
            "side_roi": 0.024, "side_sl": -0.015
        },
        "DOGE/USDT:USDT": {
            "v_factor": 5.795, "pulse_change": 0.005,
            "bull_roi": 0.121, "bull_sl": -0.099,
            "bear_roi": 0.04, "bear_sl": -0.046,
            "side_roi": 0.024, "side_sl": -0.034
        },
        "AVAX/USDT:USDT": {
            "v_factor": 5.692, "pulse_change": 0.005,
            "bull_roi": 0.112, "bull_sl": -0.092,
            "bear_roi": 0.01, "bear_sl": -0.053,
            "side_roi": 0.013, "side_sl": -0.023
        },
        "LINK/USDT:USDT": {
            "v_factor": 5.671, "pulse_change": 0.005,
            "bull_roi": 0.139, "bull_sl": -0.139,
            "bear_roi": 0.038, "bear_sl": -0.041,
            "side_roi": 0.017, "side_sl": -0.034
        },
        "DOT/USDT:USDT": {
            "v_factor": 5.051, "pulse_change": 0.001,
            "bull_roi": 0.106, "bull_sl": -0.082,
            "bear_roi": 0.032, "bear_sl": -0.044,
            "side_roi": 0.015, "side_sl": -0.02
        },
        "SUI/USDT:USDT": {
            "v_factor": 5.508, "pulse_change": 0.001,
            "bull_roi": 0.049, "bull_sl": -0.112,
            "bear_roi": 0.022, "bear_sl": -0.036,
            "side_roi": 0.014, "side_sl": -0.018
        },
        "NEAR/USDT:USDT": {
            "v_factor": 2.772, "pulse_change": 0.001,
            "bull_roi": 0.140, "bull_sl": -0.071,
            "bear_roi": 0.014, "bear_sl": -0.047,
            "side_roi": 0.011, "side_sl": -0.026
        }
    }

    # Parámetros cargados desde la configuración (JSON manda)
    v_factor = DecimalParameter(1.5, 6.0, default=4.319, space="buy", load=True, optimize=False)
    pulse_change = DecimalParameter(0.0005, 0.005, default=0.004, space="buy", load=True, optimize=False)

    def get_dna_value(self, pair: str, key: str, default: any) -> any:
        """Extrae un valor específico del ADN de la moneda o usa el default."""
        return self.hyperopt_dna.get(pair, {}).get(key, default)

    def get_v_factor(self, pair: str) -> float:
        """Retorna el v_factor oficial o un valor defensivo alto."""
        return self.get_dna_value(pair, "v_factor", 6.0)


    # --- LEVERAGE DINÁMICO (PEGASO REAL-TIME RISK) ---
    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:
        """
        Apalancamiento Mutable: 
        - Tendencia (ADX > 25): 5x (Agresivo)
        - Lateral (ADX < 25): 2x (Conservador)
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) > 0:
                last_candle = dataframe.iloc[-1]
                if last_candle['adx'] < 25:
                    return 2.0
            return 5.0
        except Exception:
            return 2.0

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

        # Bloqueo Fin de Semana (Sábado = 5, Domingo = 6)
        dataframe['day_of_week'] = dataframe['date_utc'].dt.dayofweek
        dataframe['is_weekend'] = 0
        dataframe.loc[dataframe['day_of_week'] >= 5, 'is_weekend'] = 1

        # Todo es Modo Hunter: Solo en ventana y NO en fin de semana.
        dataframe['gate_open'] = 0
        dataframe.loc[(dataframe["is_pulse_window"] == 1) & (dataframe["is_weekend"] == 0), 'gate_open'] = 1

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
            
            # Obtener parámetros del ADN para esta moneda
            dna = self.hyperopt_dna.get(pair, {})
            bull_sl = dna.get("bull_sl", self.bull_stoploss.value)
            bear_sl = dna.get("bear_sl", self.bear_stoploss.value)
            side_sl = dna.get("side_sl", self.sideways_stoploss.value)

            # BULL: Mercado alcista fuerte (ADX > 25 y RSI > 55)
            if adx > 25 and rsi > 55:
                return bull_sl
            
            # BEAR: Mercado bajista fuerte (ADX > 25 y RSI < 45)
            elif adx > 25 and rsi < 45:
                return bear_sl
            
            # LATERAL: Sin tendencia clara (ADX < 25)
            else:
                return side_sl
        except Exception as e:
            # Si falla la detección, usar stoploss estático de seguridad
            return self.stoploss

    # Límite de tiempo mutable (en minutos)
    trade_duration_max = IntParameter(60, 480, default=240, space='sell', optimize=True)

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Salida dinámica basada en régimen de mercado.
        Usa ROI específico para cada tipo de mercado y duración mutable.
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 1:
                return None
            
            last_candle = dataframe.iloc[-1].squeeze()
            adx = last_candle.get('adx', 0)
            rsi = last_candle.get('rsi', 50)
            
            # --- LÓGICA DE CIERRE POR TIEMPO MUTABLE ---
            trade_duration = (current_time - trade.open_date_utc).total_seconds() / 60
            if trade_duration >= self.trade_duration_max.value:
                return "time_exhaustion_mutable"

            # Nota: El cierre por fin de ventana (Londres/NY) se gestiona vía Vigilante externo.

            # Determinar ROI objetivo según régimen
            # Determinar ROI objetivo según régimen y ADN
            dna = self.hyperopt_dna.get(pair, {})
            bull_roi = dna.get("bull_roi", self.bull_roi_0.value)
            bear_roi = dna.get("bear_roi", self.bear_roi_0.value)
            side_roi = dna.get("side_roi", self.sideways_roi_0.value)

            if adx > 25 and rsi > 55:
                # BULL: Buscar ganancias mayores
                roi_target = bull_roi
                reason = "bull_roi_dna"
            elif adx > 25 and rsi < 45:
                # BEAR: Tomar ganancias rápido (modo defensivo)
                roi_target = bear_roi
                reason = "bear_roi_dna"
            else:
                # LATERAL: Scalping (ganancias pequeñas pero frecuentes)
                roi_target = side_roi
                reason = "sideways_roi_dna"
            
            # Salir si alcanzamos el objetivo de ROI para este régimen
            if current_profit >= roi_target:
                return reason
            
            return None
        except Exception as e:
            return None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        
        # --- LÓGICA DE MUTABILIDAD CONTINUA (PEGASO 4.0) ---
        # Interpolación lineal entre Sideways (ADX 15) y Trend (ADX 35)
        # Esto permite que el v_factor se adapte fluido vela a vela.
        
        # 1. Normalizar ADX entre 0 (Lateral) y 1 (Tendencia) con límites 15-35
        adx_norm = (dataframe['adx'] - 15) / (35 - 15)
        adx_norm = adx_norm.clip(0, 1)
        
        # 2. Calcular Multiplicador Dinámico
        # v_factor_mult = mult_side + adx_norm * (mult_trend - mult_side)
        mult_diff = self.v_factor_mult_trend.value - self.v_factor_mult_sideways.value
        dataframe['dynamic_mult'] = self.v_factor_mult_sideways.value + (adx_norm * mult_diff)
        
        # 3. v_factor y pulse_change Adaptativo por moneda
        dna_v_factor = self.get_v_factor(metadata['pair'])
        dna_pulse = self.get_dna_value(metadata['pair'], "pulse_change", self.pulse_change.value)
        
        dataframe['v_factor_eff'] = dna_v_factor * dataframe['dynamic_mult']

        # LONG: Ventana + Vol Spike (Adaptabilidad Continua) + Precio Up
        pulse_long = (
            (dataframe['gate_open'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * dataframe['v_factor_eff'])) &
            (dataframe['price_change'] > dna_pulse) &
            (dataframe['rsi'] < 80)
        )
        
        dataframe.loc[pulse_long, 'enter_long'] = 1
        dataframe.loc[pulse_long, 'enter_tag'] = 'PULSE_LONG'

        return dataframe

    def populate_entry_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_short'] = 0
        
        # Lógica de v_factor_eff adaptativa y pulso específico por moneda
        dna_v_factor = self.get_v_factor(metadata['pair'])
        dna_pulse = self.get_dna_value(metadata['pair'], "pulse_change", self.pulse_change.value)
        
        adx_norm = (dataframe['adx'] - 15) / (35 - 15)
        adx_norm = adx_norm.clip(0, 1)
        mult_diff = self.v_factor_mult_trend.value - self.v_factor_mult_sideways.value
        dataframe['dynamic_mult'] = self.v_factor_mult_sideways.value + (adx_norm * mult_diff)
        dataframe['v_factor_eff'] = dna_v_factor * dataframe['dynamic_mult']
        
        # SHORT: Ventana + Vol Spike Adaptativo + Precio Down + RSI Relajado
        pulse_short = (
            (dataframe['gate_open'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * dataframe['v_factor_eff'])) &
            (dataframe['price_change'] < -dna_pulse) &
            (dataframe['rsi'] > 10)  # Mantengo sensibilidad de 10 para cazar momentum bajista
        )
        
        dataframe.loc[pulse_short, 'enter_short'] = 1
        dataframe.loc[pulse_short, 'enter_tag'] = 'PULSE_SHORT'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_exit_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
