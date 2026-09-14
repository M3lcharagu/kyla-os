"""Risk guards, realized PnL and broker-aware position sizing."""
from datetime import datetime, timezone
from math import floor
from zoneinfo import ZoneInfo

class RiskManager:
    def __init__(self, config, symbol, initial_balance=None, symbol_info=None):
        self.config=config or {}; self.risk=self.config.get("risk",{}); self.session=self.config.get("session",{}); self.symbol=symbol
        self.instrument=self.config.get("instruments",{}).get(symbol,{})
        self.initial_balance=float(initial_balance if initial_balance is not None else self.config.get("account",{}).get("initial_balance",5000)); self.balance=self.initial_balance
        self.trades=[]; self.entries=[]; self.week_peak={}; self.symbol_info=symbol_info
    def _dt(self, value):
        if isinstance(value,(int,float)): value=datetime.fromtimestamp(value,timezone.utc)
        elif hasattr(value,"to_pydatetime"): value=value.to_pydatetime()
        elif not isinstance(value,datetime): value=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        z=ZoneInfo(self.config.get("market",{}).get("timezone","UTC")); return value.replace(tzinfo=z) if value.tzinfo is None else value.astimezone(z)
    def _day(self,t): return self._dt(t).date()
    def _week(self,t): return self._dt(t).date().isocalendar()[:2]
    def in_session(self,t):
        x=self._dt(t); 
        if x.weekday() not in self.session.get("days",[0,1,2,3]): return False
        for w in self.session.get("windows",["08:00-18:00"]):
            a,b=w.split("-",1)
            if a <= x.strftime("%H:%M") <= b: return True
        return False
    def _day_pnl(self,t): return sum(x["pnl"] for x in self.trades if self._day(x["timestamp"])==self._day(t))
    def _week_pnl(self,t): return sum(x["pnl"] for x in self.trades if self._week(x["timestamp"])==self._week(t))
    def _protected(self,t):
        w=self._week(t); self.week_peak[w]=max(self.week_peak.get(w,self.initial_balance),self.balance)
        return self._week_pnl(t)>=float(self.risk.get("weekly_target",150)) or self.week_peak[w]-self.balance>=float(self.risk.get("weekly_trailing_drawdown",50))
    def can_open(self,t):
        return self.in_session(t) and sum(self._day(x) == self._day(t) for x in self.entries) < int(self.risk.get("max_trades_per_day",3)) and self._day_pnl(t) > -float(self.risk.get("max_daily_loss",100)) and not self._protected(t)
    def register_entry(self,t):
        if not self.can_open(t): return False
        self.entries.append(self._dt(t)); return True
    def record_trade(self,pnl,t):
        stamp=self._dt(t); self.balance+=float(pnl); w=self._week(stamp); self.week_peak[w]=max(self.week_peak.get(w,self.initial_balance),self.balance)
        row={"timestamp":stamp.isoformat(),"pnl":float(pnl),"balance":self.balance}; self.trades.append(row); return row
    def status(self,t):
        x=self._dt(t); w=self._week(x)
        return {"timestamp":x.isoformat(),"symbol":self.symbol,"balance":self.balance,"day_pnl":self._day_pnl(x),"week_pnl":self._week_pnl(x),"trades_today":sum(self._day(e)==x.date() for e in self.entries),"in_session":self.in_session(x),"can_open":self.can_open(x),"weekly_peak":self.week_peak.get(w,self.initial_balance),"trade_count":len(self.trades)}

def position_size(entry, stop, account_balance, risk_config, instrument, symbol_info=None):
    distance=abs(float(entry)-float(stop));
    if distance<=0: return 0.0
    tick_size=getattr(symbol_info,"trade_tick_size",None) if symbol_info else None; tick_value=getattr(symbol_info,"trade_tick_value",None) if symbol_info else None
    cash_per_lot=distance/float(tick_size)*float(tick_value) if tick_size and tick_value and float(tick_size)>0 and float(tick_value)>0 else distance*float(instrument.get("backtest_cash_per_price_unit_per_lot",0))
    if cash_per_lot<=0: return 0.0
    raw=float(account_balance)*float(risk_config.get("risk_per_trade",.0025))/cash_per_lot
    mn=float(getattr(symbol_info,"volume_min",instrument.get("volume_min",.01)) or instrument.get("volume_min",.01)); mx=float(getattr(symbol_info,"volume_max",instrument.get("volume_max",100)) or instrument.get("volume_max",100)); step=float(getattr(symbol_info,"volume_step",instrument.get("volume_step",.01)) or instrument.get("volume_step",.01))
    lots=min(mx,floor(raw/step+1e-12)*step); return round(lots,8) if lots>=mn else 0.0
