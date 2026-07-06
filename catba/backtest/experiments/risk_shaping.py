"""#2 Risk-shaping for the Darwinex D-Score. Darwinex VaR-normalizes, so raw
return LEVEL doesn't score — CONSISTENCY of risk & returns does (Ra risk
stability, Dp durability). Question: does a different sizing/compounding rule
make CatBa's return STREAM steadier (higher Sharpe, lower vol-of-vol, shallower
worst month) without changing the underlying trades?

We take the per-trade pip outcomes (from the rich dump; profit is $ at the
backtest's fixed size) and re-express monthly returns under sizing rules:
  - FIXED $   : constant $ risk per trade (current-ish, size independent of eq)
  - EQUITY %  : compound — size scales with running equity
  - VOL-TARGET: scale each month's exposure to hit constant target vol
Then score each stream on Sharpe, vol-of-vol, worst month, max DD.
"""
import csv, math, datetime as dt
from collections import defaultdict

TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
NOM=1_600_000

def monthly_pnl():
    m=defaultdict(float)
    for r in csv.DictReader(open(TR)):
        try:
            t=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            m[(t.year,t.month)]+=float(r["profit"])
        except: continue
    return m

def curve_stats(rets):
    """rets = list of monthly returns (fraction). Sharpe, maxDD%, worst month%,
    vol-of-vol (stability of rolling 12m vol)."""
    n=len(rets); mu=sum(rets)/n
    sd=math.sqrt(sum((x-mu)**2 for x in rets)/(n-1))
    sh=mu/sd*math.sqrt(12) if sd else 0
    eq=1.0;peak=1.0;mdd=0.0
    for x in rets: eq*=(1+x); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
    worst=min(rets)
    roll=[]
    for i in range(12,n):
        w=rets[i-12:i]; m2=sum(w)/12; roll.append(math.sqrt(sum((x-m2)**2 for x in w)/11))
    vov=(math.sqrt(sum((x-sum(roll)/len(roll))**2 for x in roll)/(len(roll)-1))/(sum(roll)/len(roll))) if len(roll)>1 else 0
    posm=100*sum(1 for x in rets if x>0)/n
    return sh,mdd*100,worst*100,vov,posm

def main():
    m=monthly_pnl(); keys=sorted(m)
    # base monthly return as % of nominal (fixed-$ sizing = current backtest)
    base=[m[k]/NOM for k in keys]

    print("Sizing rule effect on the RETURN STREAM (same trades):\n")
    print(f"{'rule':<22}{'Sharpe':>8}{'maxDD%':>8}{'worstMo%':>9}{'vol-of-vol':>11}{'pos-mo%':>8}")

    # 1) FIXED $  (base)
    print(f"{'FIXED $ (current)':<22}"+"".join(f"{x:>8.2f}" if i==0 else
          (f"{x:>8.1f}" if i in(1,) else (f"{x:>9.1f}" if i==2 else (f"{x:>11.2f}" if i==3 else f"{x:>8.0f}")))
          for i,x in enumerate(curve_stats(base))))

    # 2) EQUITY % compounding — re-simulate equity, size ~ equity
    for scale in (0.5,1.0):   # 0.5% and 1% nominal-equivalent monthly aggressiveness
        eq=1.0; rets=[]
        for k in keys:
            r=(m[k]/NOM)*(eq)  # size scales with equity (compound)
            rets.append(r/eq if eq else 0)  # realized fractional return
            eq+=r
        # simpler: compounding just changes level, not Sharpe; show terminal
        eqc=1.0
        for k in keys: eqc*= (1+ m[k]/NOM)
        print(f"{'EQUITY% compound':<22}"+"".join(
            f"{x:>8.2f}" if i==0 else (f"{x:>8.1f}" if i==1 else (f"{x:>9.1f}" if i==2 else (f"{x:>11.2f}" if i==3 else f"{x:>8.0f}")))
            for i,x in enumerate(curve_stats(base)))+f"   (terminal x{eqc:.2f})")
        break

    # 3) VOL-TARGET: scale each month by target/trailing-vol (cap 1.5x)
    tgt=None
    rv=[]  # trailing 6m realized vol
    scaled=[]
    hist=[]
    for i,k in enumerate(keys):
        r=m[k]/NOM; hist.append(r)
        if len(hist)>=6:
            v=math.sqrt(sum((x-sum(hist[-6:])/6)**2 for x in hist[-6:])/5)
            if tgt is None: tgt=v
            f=min(1.5, tgt/v) if v>0 else 1.0
        else: f=1.0
        scaled.append(r*f)
    print(f"{'VOL-TARGET (6m)':<22}"+"".join(
        f"{x:>8.2f}" if i==0 else (f"{x:>8.1f}" if i==1 else (f"{x:>9.1f}" if i==2 else (f"{x:>11.2f}" if i==3 else f"{x:>8.0f}")))
        for i,x in enumerate(curve_stats(scaled))))

    print("\nNote: compounding changes WEALTH level, not Sharpe/vol-of-vol (Darwinex")
    print("VaR-normalizes level away). The D-Score lever is VOL-TARGETING — does it")
    print("cut vol-of-vol & worst month? Compare rows above.")

if __name__=="__main__":
    main()
