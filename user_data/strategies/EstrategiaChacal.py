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
    ESTRATEGIA CHACAL V1.0 - PROTOCOLO DE SUPERVIVENCIA AWS
    
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
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
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
    
    # Buy Space - Indicadores de entrada
    # Buy Space - Indicadores de entrada - RANGOS AMPLIADOS PARA MÁS TRADES
    buy_rsi = IntParameter(10, 75, default=30, space="buy")
    buy_rsi_enabled = BooleanParameter(default=True, space="buy")
    
    buy_ema_short = IntParameter(5, 30, default=9, space="buy")
    buy_ema_long = IntParameter(20, 100, default=21, space="buy")
    
    buy_volume_factor = DecimalParameter(0.1, 2.0, default=1.0, space="buy")
    buy_bb_width = DecimalParameter(0.01, 0.20, default=0.05, space="buy") # Ancho mínimo reducido, máximo aumentado
    buy_bb_percent = DecimalParameter(0.0, 0.95, default=0.3, space="buy") # Permitir compras en casi todo el rango bajo BB
    
    # Filtros de Tendencia dinámicos para el Hyperopt
    buy_trend_filter_enabled = BooleanParameter(default=False, space="buy") # Por defecto apagado para dejar entrar trades
    buy_macd_filter_enabled = BooleanParameter(default=False, space="buy") # Por defecto apagado

    # Sell Space - Indicadores de salida
    sell_rsi = IntParameter(50, 90, default=70, space="sell")
    sell_rsi_enabled = BooleanParameter(default=True, space="sell")
    sell_bb_percent = DecimalParameter(0.5, 1.0, default=0.7, space="sell")

    # Trailing Space - Optimización de trailing stop
    trailing_stop_positive_param = DecimalParameter(0.001, 0.05, default=0.005, space="sell", optimize=True, load=True)
    trailing_stop_positive_offset_param = DecimalParameter(0.005, 0.1, default=0.01, space="sell", optimize=True, load=True)

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
        # Mapeo de parámetros de Hyperopt a atributos de la estrategia
        # Esto permite optimizar el trailing stop sin romper la validación de tipos de Freqtrade
        self.trailing_stop_positive = self.trailing_stop_positive_param.value
        self.trailing_stop_positive_offset = self.trailing_stop_positive_offset_param.value

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
        conditions = []
        
        # Filtro de Tendencia Principal (Opcional por Hyperopt)
        if self.buy_trend_filter_enabled.value:
            conditions.append(dataframe['ema_short'] > dataframe['ema_long'])

        # CONDICIÓN 1: RSI
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe['rsi'] < self.buy_rsi.value)
        
        # CONDICIÓN 2: MACD (Opcional por Hyperopt)
        if self.buy_macd_filter_enabled.value:
            conditions.append(dataframe['macdhist'] > 0)
        
        # CONDICIÓN 3: Bollinger
        conditions.append(dataframe['bb_percent'] < self.buy_bb_percent.value)
        
        # CONDICIÓN 4: Volumen
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
        
        # Filtro de Tendencia Short (Opcional por Hyperopt)
        if self.buy_trend_filter_enabled.value:
            conditions.append(dataframe['ema_short'] < dataframe['ema_long'])

        # CONDICIÓN 1: RSI
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe['rsi'] > self.sell_rsi.value)
        
        # CONDICIÓN 2: MACD (Opcional por Hyperopt)
        if self.buy_macd_filter_enabled.value:
            conditions.append(dataframe['macdhist'] < 0)
        
        # CONDICIÓN 3: Bollinger
        conditions.append(dataframe['bb_percent'] > self.sell_bb_percent.value)
        
        # CONDICIÓN 4: Volumen
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
