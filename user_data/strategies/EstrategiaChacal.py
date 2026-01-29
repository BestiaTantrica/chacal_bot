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
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce


class EstrategiaChacal(IStrategy):
    """
    ESTRATEGIA CHACAL V1.0 - PROTOCOLO DE SUPERVIVENCIA O.C.I.
    
    Arquitectura:
    - Optimizada para instancias de 1GB RAM + 4GB SWAP
    - Enfoque en eficiencia algorítmica y gestión estricta de memoria
    - Objetivo: 1% diario con máxima estabilidad
    
    Filosofía: "El Chacal no persigue. Espera el momento exacto."
    """
    
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # ROI table: Objetivo 1% diario, configuración conservadora
    minimal_roi = {
        "0": 0.015,   # 1.5% ganancia objetivo
        "15": 0.012,  # 1.2% después de 15 min
        "30": 0.01,   # 1.0% después de 30 min
        "60": 0.005   # 0.5% como mínimo absoluto
    }

    # Stoploss óptimo para protección de capital
    stoploss = -0.03  # -3% pérdida máxima

    # Trailing stop: Asegurar ganancias
    trailing_stop = True
    trailing_stop_positive = 0.005  # Activar cuando hay +0.5%
    trailing_stop_positive_offset = 0.01  # Comenzar a seguir en +1%
    trailing_only_offset_is_reached = True

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # HYPEROPT SPACES - Optimización Bayesiana para recursos limitados
    
    # Buy Space - Indicadores de entrada conservadores
    buy_rsi = IntParameter(20, 40, default=30, space="buy")
    buy_rsi_enabled = BooleanParameter(default=True, space="buy")
    
    buy_ema_short = IntParameter(5, 20, default=9, space="buy")
    buy_ema_long = IntParameter(20, 50, default=21, space="buy")
    
    buy_volume_factor = DecimalParameter(1.0, 3.0, default=1.5, space="buy")
    
    # Sell Space - Indicadores de salida
    sell_rsi = IntParameter(60, 80, default=70, space="sell")
    sell_rsi_enabled = BooleanParameter(default=True, space="sell")

    # Trailing Space - Optimización de trailing stop
    trailing_stop_positive_param = DecimalParameter(0.001, 0.02, default=0.005, space="trailing")
    trailing_stop_positive_offset_param = DecimalParameter(0.005, 0.03, default=0.01, space="trailing")

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Añade varios indicadores técnicos a un DataFrame dado
        
        Optimización de memoria: Usa solo indicadores esenciales
        """

        # RSI - Índice de Fuerza Relativa (sobrecompra/sobreventa)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # EMAs - Medias Móviles Exponenciales
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod=self.buy_ema_short.value)
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=self.buy_ema_long.value)
        
        # MACD - Convergencia/Divergencia de Medias Móviles
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # Bollinger Bands - Bandas de volatilidad
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_percent'] = (
            (dataframe['close'] - dataframe['bb_lowerband']) /
            (dataframe['bb_upperband'] - dataframe['bb_lowerband'])
        )
        dataframe['bb_width'] = (
            (dataframe['bb_upperband'] - dataframe['bb_lowerband']) / dataframe['bb_middleband']
        )

        # Volume - Factor de volumen relativo
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=20).mean()

        return dataframe

    # Can this strategy go short?
    can_short: bool = True

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Basado en indicadores de TA, popula la señal de compra (buy/long)
        Filosofía Chacal: Entradas precisas en zonas de sobreventa
        """
        conditions = []
        
        # CONDICIÓN 1: RSI en sobreventa
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe['rsi'] < self.buy_rsi.value)
        
        # CONDICIÓN 2: Cruce alcista de EMAs
        conditions.append(
            qtpylib.crossed_above(dataframe['ema_short'], dataframe['ema_long'])
        )
        
        # CONDICIÓN 3: MACD alcista
        conditions.append(dataframe['macdhist'] > 0)
        
        # CONDICIÓN 4: Bollinger Low
        conditions.append(dataframe['bb_percent'] < 0.3)
        
        # CONDICIÓN 5: Volumen
        conditions.append(
            dataframe['volume'] > (dataframe['volume_mean'] * self.buy_volume_factor.value)
        )
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_long'] = 1

        return dataframe

    def populate_entry_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Basado en indicadores de TA, popula la señal de venta en corto (short)
        Filosofía Chacal: Entradas precisas en zonas de sobrecompra (Espejo de Long)
        """
        conditions = []
        
        # CONDICIÓN 1: RSI en sobrecompra
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe['rsi'] > self.sell_rsi.value)
        
        # CONDICIÓN 2: Cruce bajista de EMAs (Short cruza abajo de Long)
        conditions.append(
            qtpylib.crossed_below(dataframe['ema_short'], dataframe['ema_long'])
        )
        
        # CONDICIÓN 3: MACD bajista
        conditions.append(dataframe['macdhist'] < 0)
        
        # CONDICIÓN 4: Bollinger High
        conditions.append(dataframe['bb_percent'] > 0.7)
        
        # CONDICIÓN 5: Volumen
        conditions.append(
            dataframe['volume'] > (dataframe['volume_mean'] * self.buy_volume_factor.value)
        )
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Salida de Longs (Cierre de posición)
        """
        conditions = []
        
        # RSI en sobrecompra (señal de reversión)
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe['rsi'] > self.sell_rsi.value)
        
        # Cruce bajista
        conditions.append(
            qtpylib.crossed_below(dataframe['ema_short'], dataframe['ema_long'])
        )
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_long'] = 1

        return dataframe

    def populate_exit_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Salida de Shorts (Cierre de posición)
        """
        conditions = []
        
        # RSI en sobreventa (señal de reversión al alza)
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe['rsi'] < self.buy_rsi.value)
        
        # Cruce alcista
        conditions.append(
            qtpylib.crossed_above(dataframe['ema_short'], dataframe['ema_long'])
        )
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_short'] = 1

        return dataframe
