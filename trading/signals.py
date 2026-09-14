"""Causal ICT-inspired feature and signal calculations."""
import pandas as pd

def _p(c): return {**(c or {}).get("risk", {}), **(c or {}).get("strategy", {})}
def add_features(data, config=None):
    f = data.copy(); f.columns = [str(x).lower() for x in f.columns]
    need = {"open","high","low","close"}
    if not need.issubset(f.columns): raise ValueError(f"OHLC data missing: {sorted(need-set(f.columns))}")
    p = _p(config); pc = f.close.shift(1)
    f["tr"] = pd.concat([f.high-f.low, (f.high-pc).abs(), (f.low-pc).abs()], axis=1).max(axis=1)
    f["atr"] = f.tr.rolling(int(p.get("atr_period",14)), min_periods=int(p.get("atr_period",14))).mean()
    f["ema"] = f.close.ewm(span=int(p.get("ema_period",20)), min_periods=int(p.get("ema_period",20)), adjust=False).mean()
    r = (f.high-f.low).replace(0, pd.NA)
    f["body_ratio"] = (f.close-f.open).abs()/r
    f["loc_long"] = (f.close-f.low)/r; f["loc_short"] = (f.high-f.close)/r
    f["bullish_fvg"] = f.low > f.high.shift(2); f["bearish_fvg"] = f.high < f.low.shift(2)
    return f

def signal_at(data, evaluated, config=None):
    f = data if {"ema","atr","body_ratio"}.issubset(data.columns) else add_features(data, config)
    pos = int(evaluated) if isinstance(evaluated, int) else next((i for i,x in enumerate(f.index) if x == evaluated), -1)
    p = _p(config); n = int(p.get("sweep_lookback",5))
    if pos < max(n,2) or pos >= len(f): return None
    x = f.iloc[pos]
    if pd.isna(x.ema) or pd.isna(x.atr) or float(x.body_ratio) < float(p.get("min_body_ratio",.5)): return None
    lo, hi = f.iloc[pos-n:pos].low.min(), f.iloc[pos-n:pos].high.max()
    loc = float(p.get("min_close_location",.6)); buffer = float(p.get("stop_buffer_points",2))*float((config or {}).get("_point",1))
    if x.low < lo and x.close > lo and x.close > x.ema and bool(x.bullish_fvg) and float(x.loc_long) >= loc:
        direction, stop = "long", float(x.low)-buffer
    elif x.high > hi and x.close < hi and x.close < x.ema and bool(x.bearish_fvg) and float(x.loc_short) >= loc:
        direction, stop = "short", float(x.high)+buffer
    else: return None
    return {"direction":direction,"signal_index":pos,"signal_time":x.get("time", f.index[pos]),"stop":stop,"atr":float(x.atr),"close":float(x.close)}
