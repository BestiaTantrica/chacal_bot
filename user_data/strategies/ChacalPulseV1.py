# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timezone
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

class ChacalPulseV1(IStrategy):
    """
    ESTRATEGIA CHACAL PULSE V1 - MOLECULAR (FUTURES READY)
    
    Enfoque: Momentum de alta resolución (1m) durante aperturas de mercados globales.
    MODO: LONG & SHORT (Porque en Futures se caza en ambas direcciones).
    """
    
    INTERFACE_VERSION = 3
    can_short: bool = True

    # ROI Corto para scalping de alta frecuencia
    minimal_roi = {
        "0": 0.008,
        "5": 0.004,
        "15": 0.002,
        "30": 0.001
    }

    stoploss = -0.015 # Ajustado a -1.5% para proteger la cuenta
    
    trailing_stop = True
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.005
    trailing_only_offset_is_reached = True

    timeframe = '1m'
    
    # Parámetros Hyperoptables
    v_factor = DecimalParameter(1.5, 4.0, default=2.8, space="buy", optimize=True)
    pulse_change = DecimalParameter(0.0005, 0.003, default=0.001, space="buy", optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=7)
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=20).mean()
        
        # Ventanas de Pulso (UTC)
        dataframe['date_utc'] = pd.to_datetime(dataframe['date'], utc=True)
        dataframe['hour'] = dataframe['date_utc'].dt.hour
        dataframe['minute'] = dataframe['date_utc'].dt.minute
        
        dataframe['market_pulse_window'] = 0
        # London + NY Open
        dataframe.loc[
            ((dataframe['hour'] >= 8) & (dataframe['hour'] < 10)) | 
            ((dataframe['hour'] == 13) & (dataframe['minute'] >= 30)) | 
            ((dataframe['hour'] == 14)) | 
            ((dataframe['hour'] == 15) & (dataframe['minute'] <= 30)), 
            'market_pulse_window'
        ] = 1

        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        
        # LONG: Ventana + Vol Spike + Precio Up
        pulse_long = (
            (dataframe['market_pulse_window'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.v_factor.value)) &
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
            (dataframe['market_pulse_window'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.v_factor.value)) &
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
