"""Causal OHLC backtester; config.yaml is JSON-compatible."""
import argparse,json
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
try:
 from .signals import add_features,signal_at
 from .risk import RiskManager,position_size
except ImportError:
 from signals import add_features,signal_at
 from risk import RiskManager,position_size

def load_config(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def load_csv(path,zone):
 f=pd.read_csv(path); c=next((x for x in ("time","datetime","date") if x in f.columns),None)
 if c is None: raise ValueError("CSV must contain time, datetime, or date")
 f.columns=[str(x).lower() for x in f.columns]; t=pd.to_datetime(f[c],errors="raise")
 f["time"]=t.dt.tz_localize(ZoneInfo(zone)) if t.dt.tz is None else t.dt.tz_convert(ZoneInfo(zone))
 for x in ("open","high","low","close"): f[x]=pd.to_numeric(f[x],errors="raise")
 return f.sort_values("time").reset_index(drop=True)
def pnl(t,price,size,cfg):
 unit=float(cfg["instruments"][t["symbol"]]["backtest_cash_per_price_unit_per_lot"]); gross=((price-t["entry"]) if t["direction"]=="long" else (t["entry"]-price))*size*unit
 return gross-float(cfg.get("risk",{}).get("commission_per_lot",0))*size
def run_backtest(frame,symbol,cfg):
 cfg={**cfg,"_point":cfg["instruments"][symbol].get("point",1)}; f=add_features(frame,cfg); rm=RiskManager(cfg,symbol); trades=[]; opened=None; curve=[]; rr=float(cfg.get("risk",{}).get("reward_to_risk",1.5))
 if not len(f): return {"symbol":symbol,"summary":{"initial_balance":rm.initial_balance,"final_balance":rm.balance,"trades":0,"wins":0,"losses":0,"win_rate":0,"profit_factor":0,"net_pnl":0,"max_drawdown":0,"equity_curve":[]},"trades":[]}
 curve.append({"time":f.iloc[0].time.isoformat(),"equity":rm.balance})
 for i in range(1,len(f)):
  r=f.iloc[i]
  if opened:
   sh=(r.low<=opened["stop"]) if opened["direction"]=="long" else (r.high>=opened["stop"]); th=(r.high>=opened["target"]) if opened["direction"]=="long" else (r.low<=opened["target"])
   if sh or th:
    price,reason=(opened["stop"],"stop") if sh else (opened["target"],"target"); value=pnl(opened,price,opened["size"],cfg); rm.record_trade(value,r.time); trades.append({**opened,"exit":price,"exit_time":r.time.isoformat(),"reason":reason,"pnl":value}); opened=None
  if opened is None:
   s=signal_at(f,i-1,cfg)
   if s and rm.can_open(r.time):
    entry=float(r.open); stop=float(s["stop"]); valid=stop<entry if s["direction"]=="long" else stop>entry; size=position_size(entry,stop,rm.balance,rm.risk,cfg["instruments"][symbol]) if valid else 0
    if size>0 and rm.register_entry(r.time):
     d=abs(entry-stop); target=entry+rr*d if s["direction"]=="long" else entry-rr*d; opened={"symbol":symbol,"direction":s["direction"],"signal_time":str(s["signal_time"]),"entry_time":r.time.isoformat(),"entry":entry,"stop":stop,"target":target,"size":size}
  curve.append({"time":r.time.isoformat(),"equity":rm.balance})
 if opened:
  r=f.iloc[-1]; value=pnl(opened,float(r.close),opened["size"],cfg); rm.record_trade(value,r.time); trades.append({**opened,"exit":float(r.close),"exit_time":r.time.isoformat(),"reason":"end_of_data","pnl":value})
 ps=[float(x["pnl"]) for x in trades]; wins=[x for x in ps if x>0]; losses=[x for x in ps if x<0]; peak=rm.initial_balance; dd=0
 for e in curve: peak=max(peak,e["equity"]); dd=max(dd,peak-e["equity"])
 summary={"initial_balance":rm.initial_balance,"final_balance":rm.balance,"trades":len(ps),"wins":len(wins),"losses":len(losses),"win_rate":len(wins)/len(ps) if ps else 0.0,"profit_factor":sum(wins)/abs(sum(losses)) if losses else (float("inf") if wins else 0.0),"net_pnl":sum(ps),"max_drawdown":dd,"equity_curve":curve}
 return {"symbol":symbol,"summary":summary,"trades":trades}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--csv",required=True); p.add_argument("--symbol",required=True,choices=("XAUUSD","US100")); p.add_argument("--config",default=str(Path(__file__).with_name("config.yaml"))); p.add_argument("--output"); a=p.parse_args(); result=run_backtest(load_csv(a.csv,load_config(a.config)["market"]["timezone"]),a.symbol,load_config(a.config)); text=json.dumps(result,indent=2,default=str,allow_nan=False); Path(a.output).write_text(text+"\n") if a.output else print(text)
if __name__=="__main__": main()
