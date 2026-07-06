"""Intraday / SESSION structure on GBPJPY — the last orthogonal edge family
untested (a daily EMA system like CatBa can't capture within-day structure).

Three pre-registered probes (IS 2016-21 / OOS 2022-26):
  A) Hour-of-day seasonality: mean H1 return per server-hour. Persistent
     directional edge in specific hours? (IS vs OOS must agree.)
  B) London-expansion: Asian session sets a range; London breaks it and
     CONTINUES (ICT judas/expansion) or FADES. Trade the break direction to
     end of London. Standalone edge + OOS.
  C) Correlation of best session edge's monthly P&L to CatBa (want low).

Server time = MT5 broker time (~GMT+2/3). Sessions identified data-drivenly
from per-hour volatility. P&L in pips, no stop (proxy).
"""
import csv, math, datetime as dt
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
PIP=0.01; NOM=1_600_000

def h1():
    out=[]
    for r in csv.reader(open(fr"{CF}\smt_GBPJPY_H1.csv")):
        if not r or r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        out.append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    return out

def sharpe(v):
    if len(v)<3: return 0.0
    mu=sum(v)/len(v); sd=math.sqrt(sum((x-mu)**2 for x in v)/(len(v)-1))
    return mu/sd*math.sqrt(12) if sd else 0.0

def main():
    B=h1()
    # --- A) hour-of-day seasonality + per-hour vol ---
    ret=defaultdict(list); vol=defaultdict(list); ret_oos=defaultdict(list); ret_is=defaultdict(list)
    for t,o,h,l,c in B:
        r=(c-o)/PIP
        ret[t.hour].append(r); vol[t.hour].append((h-l)/PIP)
        (ret_is if t.year<=2021 else ret_oos)[t.hour].append(r)
    print("=== A) Hour-of-day (server) — mean H1 return (pips) & range ===")
    print(f"{'hr':>3}{'meanRet':>9}{'IS':>8}{'OOS':>8}{'avgRange':>10}{'n':>7}")
    for hh in range(24):
        if not ret[hh]: continue
        mr=sum(ret[hh])/len(ret[hh])
        mi=sum(ret_is[hh])/len(ret_is[hh]) if ret_is[hh] else 0
        mo=sum(ret_oos[hh])/len(ret_oos[hh]) if ret_oos[hh] else 0
        av=sum(vol[hh])/len(vol[hh])
        agree="  <=IS/OOS agree" if (mi>0)==(mo>0) and abs(mr)>0.3 else ""
        print(f"{hh:>3}{mr:>+9.2f}{mi:>+8.2f}{mo:>+8.2f}{av:>10.1f}{len(ret[hh]):>7}{agree}")

    # --- B) London-expansion: Asian range (server 1-8) -> London (9-16) ---
    days=defaultdict(list)
    for b in B: days[b[0].date()].append(b)
    ASIA=range(1,9); LON=range(9,17)
    trades=[]   # (date, pnl_pips, dir)
    for d in sorted(days):
        bl=sorted(days[d]); byh={b[0].hour:b for b in bl}
        ab=[byh[h] for h in ASIA if h in byh]; lb=[byh[h] for h in LON if h in byh]
        if len(ab)<4 or len(lb)<4: continue
        ahi=max(x[2] for x in ab); alo=min(x[3] for x in ab)
        lon_open=lb[0][1]; lon_close=lb[-1][4]
        # first London bar that breaks Asian hi or lo -> trade break dir to close
        dirn=0
        for x in lb:
            if x[2]>ahi: dirn=+1; brk=ahi; break
            if x[3]<alo: dirn=-1; brk=alo; break
        if not dirn: continue
        pnl=dirn*(lon_close-brk)/PIP
        trades.append((d,pnl,dirn))
    tot=sum(p for _,p,_ in trades); wr=100*sum(1 for _,p,_ in trades if p>0)/len(trades)
    is_=[p for d,p,_ in trades if d.year<=2021]; oos=[p for d,p,_ in trades if d.year>2021]
    print(f"\n=== B) London breaks Asian range -> continue to London close ===")
    print(f"{len(trades)} days  net {tot:+.0f}p  win {wr:.1f}%  "
          f"IS {sum(is_):+.0f}p  OOS {sum(oos):+.0f}p")
    # fade variant
    fade=[(d,-p) for d,p,_ in trades]
    print(f"  FADE variant: net {sum(p for _,p in fade):+.0f}p  "
          f"OOS {sum(p for d,p in fade if d.year>2021):+.0f}p")

    # monthly series of London-breakout + correlation to CatBa
    lm=defaultdict(float)
    for d,p,_ in trades: lm[(d.year,d.month)]+=p
    cb=defaultdict(float)
    for r in csv.DictReader(open(TR)):
        try:
            t=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            cb[(t.year,t.month)]+=float(r["profit"])
        except: continue
    keys=sorted(set(cb)|set(lm)); n=len(keys)
    a=[cb.get(k,0)/NOM*100 for k in keys]; bvec=[lm.get(k,0) for k in keys]
    ma=sum(a)/n; mb=sum(bvec)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a)/n) or 1; sb=math.sqrt(sum((x-mb)**2 for x in bvec)/n) or 1
    corr=sum((a[i]-ma)*(bvec[i]-mb) for i in range(n))/n/(sa*sb)
    print(f"\nLondon-breakout monthly Sharpe {sharpe(bvec):.2f} "
          f"(IS {sharpe([bvec[i] for i in range(n) if keys[i][0]<=2021]):.2f}/"
          f"OOS {sharpe([bvec[i] for i in range(n) if keys[i][0]>2021]):.2f})  "
          f"corr to CatBa {corr:+.2f}")

if __name__=="__main__":
    main()
