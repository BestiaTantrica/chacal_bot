from datetime import datetime, timezone
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

class ChacalPulseV4_Hyperopt(IStrategy):
    """
    ESTRATEGIA CHACAL V4 (HYPEROPT) - REGIMEN ADAPTATIVO
    CON CIERRE FORZADO POST-VENTANAS MAGICAS (+15 MIN)
    """
    
    INTERFACE_VERSION = 3
    can_short: bool = True

    # --- PARÁMETROS HYPEROPTABLES POR RÉGIMEN ---
    bull_roi_0 = DecimalParameter(0.02, 0.15, default=0.023, space="sell", optimize=True)
    bull_stoploss = DecimalParameter(-0.15, -0.05, default=-0.076, space="sell", optimize=True)
    
    bear_roi_0 = DecimalParameter(0.01, 0.05, default=0.048, space="sell", optimize=True)
    bear_stoploss = DecimalParameter(-0.06, -0.02, default=-0.036, space="sell", optimize=True)
    
    sideways_roi_0 = DecimalParameter(0.005, 0.025, default=0.025, space="sell", optimize=True)
    sideways_stoploss = DecimalParameter(-0.04, -0.01, default=-0.017, space="sell", optimize=True)

    stoploss = -0.231
    timeframe = '5m'
    
    v_factor = DecimalParameter(1.5, 6.0, default=4.319, space="buy", optimize=True)
    pulse_change = DecimalParameter(0.0005, 0.005, default=0.004, space="buy", optimize=True)
    operation_mode = CategoricalParameter(['hunter', 'vigilante'], default='hunter', space="buy", optimize=True)

    def leverage(self, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']

        # Sincronización UTC para Aperturas
        dataframe['date_utc'] = pd.to_datetime(dataframe['date'], utc=True)
        dataframe['hour'] = dataframe['date_utc'].dt.hour
        dataframe['minute'] = dataframe['date_utc'].dt.minute
        
        # --- VENTANAS MAGICAS (UTC) ---
        # LONDRES: 08:00 - 10:00 UTC (05:00 - 07:00 ART)
        # NY: 13:30 - 17:30 UTC (10:30 - 14:30 ART)
        
        dataframe['is_pulse_window'] = 0
        dataframe.loc[
            ((dataframe['hour'] >= 8) & (dataframe['hour'] < 10)) | 
            ((dataframe['hour'] == 13) & (dataframe['minute'] >= 30)) |
            ((dataframe['hour'] >= 14) & (dataframe['hour'] < 17)) |
            ((dataframe['hour'] == 17) & (dataframe['minute'] <= 30)),
            'is_pulse_window'
        ] = 1

        # --- CIERRE FORZADO (ZONAS MUERTAS +15 MIN) ---
        # 1. Post-Londres: 10:15 UTC
        # 2. Post-NY: 17:45 UTC
        dataframe['force_exit_zone'] = 0
        dataframe.loc[
            ((dataframe['hour'] == 10) & (dataframe['minute'] >= 15)) | # Después de Londres
            ((dataframe['hour'] > 10) & (dataframe['hour'] < 13)) |     # Entre Londres y NY
            ((dataframe['hour'] == 13) & (dataframe['minute'] < 30)) |   # Pre-NY opening
            ((dataframe['hour'] == 17) & (dataframe['minute'] >= 45)) | # Después de NY
            ((dataframe['hour'] > 17)) |                               # Tarde/Noche UTC
            ((dataframe['hour'] < 8)),                                  # Madrugada UTC pre-Londres
            'force_exit_zone'
        ] = 1

        dataframe['gate_open'] = 0
        if self.operation_mode.value == 'hunter':
            dataframe.loc[dataframe['is_pulse_window'] == 1, 'gate_open'] = 1
        else:
            dataframe.loc[:, 'gate_open'] = 1

        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']
        
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 1: return self.stoploss
            last_candle = dataframe.iloc[-1].squeeze()
            adx = last_candle.get('adx', 0); rsi = last_candle.get('rsi', 50)
            if adx > 25 and rsi > 55: return self.bull_stoploss.value
            elif adx > 25 and rsi < 45: return self.bear_stoploss.value
            else: return self.sideways_stoploss.value
        except Exception: return self.stoploss

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Salida dinámica: Prioriza cerrar al final de la ventana mágica (+15 min).
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 1: return None
            last_candle = dataframe.iloc[-1].squeeze()

            # --- REGLA DE ORO: CIERRE POST-VENTANA (+15 min) ---
            if last_candle.get('force_exit_zone', 0) == 1:
                return "magic_window_end"

            # --- Lógica Normal de ROI ---
            adx = last_candle.get('adx', 0); rsi = last_candle.get('rsi', 50)
            if adx > 25 and rsi > 55: roi_target = self.bull_roi_0.value; reason = "bull_roi"
            elif adx > 25 and rsi < 45: roi_target = self.bear_roi_0.value; reason = "bear_roi"
            else: roi_target = self.sideways_roi_0.value; reason = "sideways_roi"
            
            if current_profit >= roi_target: return reason
            return None
        except Exception: return None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        pulse_long = (
            (dataframe['gate_open'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.v_factor.value)) &
            (dataframe['price_change'] > self.pulse_change.value) &
            (dataframe['rsi'] < 80)
        )
        dataframe.loc[pulse_long, 'enter_long'] = 1
        dataframe.loc[pulse_long, 'enter_tag'] = 'PULSE_LONG'
        return dataframe

    def populate_entry_short(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_short'] = 0
        pulse_short = (
            (dataframe['gate_open'] == 1) &
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
