"""Read-only MetaTrader 5 market-data connector."""
import os
from zoneinfo import ZoneInfo
import pandas as pd
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

TF = {x: getattr(mt5, "TIMEFRAME_" + x, None) if mt5 else None for x in ("M1","M2","M3","M4","M5","M6","M10","M12","M15","M20","M30","H1","H2","H4","D1")}

class MT5Connector:
    def __init__(self, config=None):
        self.config = config or {}
        self.zone = ZoneInfo(self.config.get("market", {}).get("timezone", "UTC"))
        self.connected = False
    def initialize(self):
        if mt5 is None: raise RuntimeError("MetaTrader5 is not installed")
        path = os.getenv("MT5_PATH")
        if not (mt5.initialize(path) if path else mt5.initialize()): raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        vals = [os.getenv(x) for x in ("MT5_LOGIN","MT5_PASSWORD","MT5_SERVER")]
        if any(x is not None for x in vals):
            if not all(vals): raise RuntimeError("MT5_LOGIN, MT5_PASSWORD and MT5_SERVER must all be set together")
            if not mt5.login(int(vals[0]), password=vals[1], server=vals[2]): raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")
        self.connected = True
    def shutdown(self):
        if mt5 is not None and self.connected: mt5.shutdown()
        self.connected = False
    def _check(self):
        if mt5 is None or not self.connected: raise RuntimeError("MT5 is not initialized")
    def symbol_select(self, symbol):
        self._check()
        if not mt5.symbol_select(symbol, True): raise RuntimeError(f"Could not select {symbol}: {mt5.last_error()}")
        return self.symbol_info(symbol)
    def symbol_info(self, symbol):
        self._check(); value = mt5.symbol_info(symbol)
        if value is None: raise RuntimeError(f"No symbol information for {symbol}")
        return value
    def tick(self, symbol):
        self._check(); value = mt5.symbol_info_tick(symbol)
        if value is None: raise RuntimeError(f"No tick for {symbol}")
        return value
    def rates(self, symbol, timeframe="M5", bars=300, skip_forming_bar=True):
        self.symbol_select(symbol)
        tf = TF.get(str(timeframe).upper())
        if tf is None: raise ValueError(f"Unsupported timeframe: {timeframe}")
        raw = mt5.copy_rates_from_pos(symbol, tf, 0, int(bars) + int(skip_forming_bar))
        if raw is None or len(raw) == 0: raise RuntimeError(f"No rates for {symbol}: {mt5.last_error()}")
        out = pd.DataFrame(raw).sort_values("time").reset_index(drop=True)
        out["time"] = pd.to_datetime(out.time, unit="s", utc=True).dt.tz_convert(self.zone)
        return out.iloc[:-1].reset_index(drop=True) if skip_forming_bar and len(out) > bars else out
    def __enter__(self): self.initialize(); return self
    def __exit__(self, *_): self.shutdown()
