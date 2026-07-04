"""
Faithful-ish Python backtest of the CatBa MT5 EA (GBPJPY H1).

Strategy (as read from CatBa.mq5):
  - Daily bias from YESTERDAY's D1 candle:
        open>close -> SELL, open<close -> BUY,
        |close-open| < minBodyYest -> NOBIAS
  - Pivots from yesterday's D1: PP=(H+L+C)/3, R1=2PP-L, S1=2PP-H
  - EMA(emaPeriod) on H1 close.
  - Max ONE trade per day. Entry checked intrabar on each H1 bar:
        BUY bias : trigger if bar LOW <= EMA - addPipsToEMA  (pullback below EMA)
                   entry=trigger px, tp=R1, sl=S1 (capped so risk<=reward)
        SELL bias: trigger if bar HIGH >= EMA + addPipsToEMA
                   entry=trigger px, tp=S1, sl=R1 (capped so risk<=reward)
  - Break-even mgmt: once price runs beToTrigger in favour, move SL to
        entry -/+ addPipToSl (locks a small profit).
  - Risk-% position sizing on equity; PnL in USD via tick value.

Notes / approximations vs the live EA:
  * Live EA checks every 12 min at market; here we use H1 OHLC and assume a
    stop-style fill at the threshold price (limit-ish). Documented, sanity-check
    later against the MT5 Strategy Tester.
  * Intrabar SL/TP/BE resolution order: if both SL and TP fall inside the same
    bar we assume SL hit first (conservative).
"""
import csv, datetime as dt
from dataclasses import dataclass, field

PIP = 0.01  # GBPJPY pip

@dataclass
class Params:
    emaPeriod: int = 8
    addPipsToEMA: float = 0.11
    minBodyYest: float = 0.28      # minPipsRequiredFromYesterday
    beToTrigger: float = 0.72      # DistanceToTriggerBE
    addPipToSl: float = 0.20       # add_pip_to_sl (BE lock)
    riskPct: float = 2.0           # % equity per trade
    capRiskToReward: bool = True   # EA caps SL so loss<=profit
    useBE: bool = True

@dataclass
class Trade:
    day: dt.date; side: str; entry_t: dt.datetime; entry: float
    sl: float; tp: float
    exit_t: dt.datetime = None; exit: float = None; reason: str = ""
    lots: float = 0.0; pnl_usd: float = 0.0; be_moved: bool = False

def load_csv(fn):
    rows=[]
    with open(fn) as f:
        for r in csv.DictReader(f):
            rows.append((dt.datetime.utcfromtimestamp(int(r["time"])),
                         float(r["open"]),float(r["high"]),float(r["low"]),
                         float(r["close"]),float(r["spread"])))
    return rows

def ema_series(closes, period):
    k=2/(period+1); out=[]; e=None
    for c in closes:
        e = c if e is None else c*k + e*(1-k)
        out.append(e)
    return out

def build_daily(h1):
    """Aggregate H1 -> D1 (UTC day) to derive yesterday bias+pivots the same
    way the EA reads iTime(D1). Keyed by date -> (o,h,l,c)."""
    d={}
    for t,o,h,l,c,sp in h1:
        day=t.date()
        if day not in d: d[day]=[o,h,l,c]
        else:
            a=d[day]; a[1]=max(a[1],h); a[2]=min(a[2],l); a[3]=c
    return d

def pip_value_per_lot(tick_size, tick_value):
    # value of 1 pip (0.01) per 1.0 lot, in account ccy
    return (PIP / tick_size) * tick_value

def backtest(h1, daily, p: Params, tick_size, tick_value,
             spread_price, start_equity=10000.0, year_filter=None):
    closes=[b[4] for b in h1]
    ema=ema_series(closes, p.emaPeriod)
    days_sorted=sorted(daily.keys())
    di={d:i for i,d in enumerate(days_sorted)}
    pipval=pip_value_per_lot(tick_size, tick_value)

    equity=start_equity
    trades=[]; open_tr=None; traded_days=set()

    for i,(t,o,h,l,c,sp) in enumerate(h1):
        day=t.date()
        # ---- manage open trade first (BE + exits) ----
        if open_tr:
            tr=open_tr
            if p.useBE and not tr.be_moved:
                if tr.side=="BUY" and (h - tr.entry) >= p.beToTrigger:
                    tr.sl=max(tr.sl, tr.entry + p.addPipToSl); tr.be_moved=True
                elif tr.side=="SELL" and (tr.entry - l) >= p.beToTrigger:
                    tr.sl=min(tr.sl, tr.entry - p.addPipToSl); tr.be_moved=True
            hit_sl = (l<=tr.sl) if tr.side=="BUY" else (h>=tr.sl)
            hit_tp = (h>=tr.tp) if tr.side=="BUY" else (l<=tr.tp)
            ex=None
            if hit_sl and hit_tp: ex=(tr.sl,"SL(both)")      # conservative
            elif hit_sl: ex=(tr.sl,"SL")
            elif hit_tp: ex=(tr.tp,"TP")
            if ex:
                tr.exit=ex[0]; tr.reason=ex[1]; tr.exit_t=t
                move = (tr.exit-tr.entry) if tr.side=="BUY" else (tr.entry-tr.exit)
                tr.pnl_usd = (move/PIP)*pipval*tr.lots
                equity+=tr.pnl_usd
                trades.append(tr); open_tr=None

        # ---- entry logic (max 1/day) ----
        if open_tr is None and day not in traded_days and day in di and di[day]>0:
            yd=days_sorted[di[day]-1]
            yo,yh,yl,yc=daily[yd]
            body=yc-yo
            bias="NOBIAS"
            if yo>yc: bias="SELL"
            elif yo<yc: bias="BUY"
            if abs(body)<p.minBodyYest: bias="NOBIAS"
            if bias!="NOBIAS":
                PP=(yh+yl+yc)/3; R1=2*PP-yl; S1=2*PP-yh
                e=ema[i]
                if bias=="BUY":
                    thr=e - p.addPipsToEMA
                    if l<=thr:                          # pullback touched
                        entry=thr+spread_price          # buy at ask
                        sl=S1; tp=R1
                        if p.capRiskToReward:
                            prof=tp-entry; loss=entry-sl
                            if loss>prof: sl=entry-prof
                        if sl<entry<tp:
                            open_tr=_open(day,"BUY",t,entry,sl,tp,equity,p,pipval)
                            traded_days.add(day)
                elif bias=="SELL":
                    thr=e + p.addPipsToEMA
                    if h>=thr:
                        entry=thr-spread_price          # sell at bid
                        sl=R1; tp=S1
                        if p.capRiskToReward:
                            prof=entry-tp; loss=sl-entry
                            if loss>prof: sl=entry+prof
                        if tp<entry<sl:
                            open_tr=_open(day,"SELL",t,entry,sl,tp,equity,p,pipval)
                            traded_days.add(day)
    return trades, equity

def _open(day,side,t,entry,sl,tp,equity,p,pipval):
    risk_usd=equity*(p.riskPct/100)
    sl_pips=abs(entry-sl)/PIP
    lots = round(risk_usd/(sl_pips*pipval),2) if sl_pips>0 else 0.0
    lots=max(lots,0.01)
    return Trade(day=day,side=side,entry_t=t,entry=entry,sl=sl,tp=tp,lots=lots)

def summarize(trades, start_equity=10000.0):
    from collections import defaultdict
    byyear=defaultdict(list)
    for tr in trades: byyear[tr.exit_t.year].append(tr)
    print(f"\n{'Year':>6} {'Trades':>7} {'Wins':>5} {'Win%':>6} {'PnL$':>12} {'CumEq$':>12}")
    eq=start_equity; total=0
    for y in sorted(byyear):
        ts=byyear[y]; w=sum(1 for t in ts if t.pnl_usd>0)
        pnl=sum(t.pnl_usd for t in ts); eq+=pnl; total+=pnl
        print(f"{y:>6} {len(ts):>7} {w:>5} {100*w/len(ts):>5.1f}% {pnl:>12,.0f} {eq:>12,.0f}")
    print(f"\nTotal trades: {len(trades)}  Net: ${total:,.0f}  Final eq: ${start_equity+total:,.0f}")
    return byyear
