# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce


class EstrategiaChacal(IStrategy):
    """
    ESTRATEGIA CHACAL V17 - CASCADE (HydroFlow)
    
    Arquitectura Cascada 50:
    - Flujo 1: Detección de Régimen (Ema200 + ADX).
    - Flujo 2: Auditoría de Impulso (ROC + BB).
    - Flujo 3: Decisión de Gatillo (Auto-Inversión por lógica de régimen).
    
    AUTONOMÍA TOTAL: No necesita intervención manual.
    """
    
    INTERFACE_VERSION = 3

    # ROI HydroFlow - Dinámico y Adaptativo
    minimal_roi = {
        "0": 0.012,     # Salida rápida 1.2%
        "15": 0.006,    # 0.6% en 15 min
        "40": 0.001     # Salida defensiva
    }

    stoploss = -0.05
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    # LEY DE HIERRO: PARA QUE EL USUARIO CONFÍE
    max_open_trades = 9
    
    process_only_new_candles = True
    startup_candle_count: int = 200

    # PARÁMETROS DE CASCADA
    # m: 0=AUTO, 1=BULL, 2=BEAR, 3=LAT
    m = IntParameter(0, 3, default=0, space="buy", optimize=False)
    # i: Inversión (0=Directo, 1=Invertido)
    i = IntParameter(0, 1, default=0, space="buy", optimize=False)
    # s: Sensibilidad (1=Muy rápido, 10=Lento) - S3 por defecto
    s = IntParameter(1, 10, default=3, space="buy", optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- CASCADA 1: INDICADORES TÉCNICOS ---
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_200'] = ta.EMA(dataframe, timeperiod=200)
        dataframe['roc'] = ta.ROC(dataframe, timeperiod=9)
        dataframe['adx'] = ta.ADX(dataframe)
        
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2.0)
        dataframe['bb_lo'] = bollinger['lower']
        dataframe['bb_up'] = bollinger['upper']
        dataframe['bb_mid'] = bollinger['mid']

        # --- CASCADA 2: AUDITORÍA DE RÉGIMEN (Auto-M) ---
        # Si el precio > EMA200 y ADX > 20 -> BULL
        # Si el precio < EMA200 y ADX > 20 -> BEAR
        # Sino -> LATERAL
        dataframe['auto_m'] = 3
        dataframe.loc[(dataframe['close'] > dataframe['ema_200']) & (dataframe['adx'] > 20), 'auto_m'] = 1
        dataframe.loc[(dataframe['close'] < dataframe['ema_200']) & (dataframe['adx'] > 20), 'auto_m'] = 2

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        
        # Orquestación de Cascada
        mode = self.m.value if self.m.value != 0 else dataframe['auto_m'].iloc[-1]
        inv = self.i.value
        sens = self.s.value * 0.12 # Factor de gatillo ajustable
        
        # AUDITORÍA DE IMPULSO
        pulse_up = (dataframe['roc'] > sens) & (dataframe['rsi'] < 65)
        
        tag = f"CASCADE_L_{'BULL' if mode==1 else ('BEAR' if mode==2 else 'LAT')}_{'INV' if inv==1 else 'NORM'}_S{self.s.value}"

        if inv == 0:
            # Solo Long en Bull o Lat
            if mode in [1, 3]:
                dataframe.loc[pulse_up, 'enter_long'] = 1
                dataframe.loc[pulse_up, 'enter_tag'] = tag
        else:
            # Si está invertido, el impulso arriba es para vender (Short)
            if mode in [2, 3]:
                dataframe.loc[pulse_up, 'enter_short'] = 1
                dataframe.loc[pulse_up, 'enter_tag'] = tag

        return dataframe

    def populate_entry_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_short'] = 0
        
        mode = self.m.value if self.m.value != 0 else dataframe['auto_m'].iloc[-1]
        inv = self.i.value
        sens = - (self.s.value * 0.12)
        
        pulse_down = (dataframe['roc'] < sens) & (dataframe['rsi'] > 35)
        
        tag = f"CASCADE_S_{'BEAR' if mode==2 else ('BULL' if mode==1 else 'LAT')}_{'INV' if inv==1 else 'NORM'}_S{self.s.value}"

        if inv == 0:
            if mode in [2, 3]:
                dataframe.loc[pulse_down, 'enter_short'] = 1
                dataframe.loc[pulse_down, 'enter_tag'] = tag
        else:
            if mode in [1, 3]:
                dataframe.loc[pulse_down, 'enter_long'] = 1
                dataframe.loc[pulse_down, 'enter_tag'] = tag

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Salida por agotamiento de impulso - DESACTIVADO para evitar sangrado
        # dataframe.loc[dataframe['roc'] < 0, 'exit_long'] = 1
        return dataframe

    def populate_exit_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe.loc[dataframe['roc'] > 0, 'exit_short'] = 1
        return dataframe
