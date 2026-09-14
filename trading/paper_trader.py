"""Read-only MT5 paper loop. It never submits an order."""
import argparse,json,time
from pathlib import Path
from mt5_connector import MT5Connector
from signals import add_features,signal_at
from risk import RiskManager,position_size

def run(symbol,cfg):
 cfg={**cfg,"_point":cfg["instruments"][symbol].get("point",1)}; con=MT5Connector(cfg); trade=None; last=None; closed=0; rm=None
 try:
  con.initialize(); info=con.symbol_info(symbol); rm=RiskManager(cfg,symbol,symbol_info=info)
  while True:
   f=add_features(con.rates(symbol,cfg["market"].get("timeframe","M5"),300,True),cfg)
   if len(f)<2: time.sleep(cfg["market"].get("poll_seconds",5)); continue
   x=f.iloc[-1]; tick=con.tick(symbol); bid,ask=float(tick.bid),float(tick.ask)
   if trade:
    sh=(x.low<=trade["stop"]) if trade["direction"]=="long" else (x.high>=trade["stop"]); th=(x.high>=trade["target"]) if trade["direction"]=="long" else (x.low<=trade["target"])
    if sh or th or not rm.in_session(x.time):
     price,why=(trade["stop"],"stop") if sh else ((trade["target"],"target") if th else ((bid if trade["direction"]=="long" else ask),"session_end")); unit=cfg["instruments"][symbol]["backtest_cash_per_price_unit_per_lot"]; value=((price-trade["entry"]) if trade["direction"]=="long" else (trade["entry"]-price))*trade["size"]*unit; rm.record_trade(value,x.time); print(json.dumps({"event":"paper_exit","reason":why,"price":price,"pnl":value,"status":rm.status(x.time)})); trade=None; closed+=1
   if last is None: last=x.time
   elif x.time!=last and trade is None:
    s=signal_at(f,len(f)-1,cfg)
    if s and rm.can_open(x.time):
     entry=ask if s["direction"]=="long" else bid; stop=float(s["stop"]); valid=stop<entry if s["direction"]=="long" else stop>entry; size=position_size(entry,stop,rm.balance,rm.risk,cfg["instruments"][symbol],info) if valid else 0
     if size>0 and rm.register_entry(x.time):
      d=abs(entry-stop); rr=cfg["risk"].get("reward_to_risk",1.5); target=entry+rr*d if s["direction"]=="long" else entry-rr*d; trade={"direction":s["direction"],"entry":entry,"stop":stop,"target":target,"size":size,"entry_time":x.time.isoformat()}; print(json.dumps({"event":"paper_entry",**trade},default=str))
    last=x.time
   print(json.dumps({"event":"status","symbol":symbol,"bid":bid,"ask":ask,"open_trade":trade,"status":rm.status(x.time)},default=str)); time.sleep(cfg["market"].get("poll_seconds",5))
 except KeyboardInterrupt:
  if trade and rm:
   t=con.tick(symbol); price=float(t.bid) if trade["direction"]=="long" else float(t.ask); unit=cfg["instruments"][symbol]["backtest_cash_per_price_unit_per_lot"]; value=((price-trade["entry"]) if trade["direction"]=="long" else (trade["entry"]-price))*trade["size"]*unit; rm.record_trade(value,t.time); print(json.dumps({"event":"paper_exit","reason":"interrupt","price":price,"pnl":value}))
  if rm: print(json.dumps({"event":"summary","closed_trades":closed+int(trade is not None),"status":rm.status(time.time())},default=str))
 finally: con.shutdown()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--symbol",required=True,choices=("XAUUSD","US100")); p.add_argument("--config",default=str(Path(__file__).with_name("config.yaml"))); a=p.parse_args(); run(a.symbol,json.loads(Path(a.config).read_text()))
if __name__=="__main__": main()
