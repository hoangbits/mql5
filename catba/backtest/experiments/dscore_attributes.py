"""Score CatBa v1.1 against Darwinex-style Investable Attributes (proxies),
so we can optimize FOR the D-Score instead of raw profit.

Darwinex VaR-normalizes, then rewards: stable risk (Ra/Rs), loss aversion
(La), consistency/durability (Dp), performance (Pf). From ref13ms_trades.
"""
import csv, math, datetime as dt
from collections import defaultdict

F = r"C:\Users\giaho\repos\mql5\catba\backtest\results\ref13ms_trades.csv"
NOM = 1_600_000

def load():
    trades=[]; monthly=defaultdict(float)
    for r in csv.DictReader(open(F)):
        try:
            t=dt.datetime.strptime(r["close_time"].strip(),"%Y.%m.%d %H:%M")
            p=float(r["profit"])+float(r["swap"])+float(r["commission"])
        except Exception: continue
        trades.append((t,p)); monthly[(t.year,t.month)]+=p
    trades.sort()
    return trades, monthly

def main():
    trades, m = load()
    pnl=[p for _,p in trades]
    # month grid
    keys=sorted(m); mr=[m[k]/NOM*100 for k in keys]   # monthly return %
    n=len(mr); mean=sum(mr)/n; sd=math.sqrt(sum((x-mean)**2 for x in mr)/(n-1))

    # --- Ra/Rs: risk (monthly vol) STABILITY over rolling windows ---
    roll=[]
    for i in range(12,n):
        w=mr[i-12:i]; mu=sum(w)/12; s=math.sqrt(sum((x-mu)**2 for x in w)/11)
        roll.append(s)
    vol_of_vol = (math.sqrt(sum((x-sum(roll)/len(roll))**2 for x in roll)/(len(roll)-1))/(sum(roll)/len(roll))) if roll else 0

    # --- La: loss aversion — payoff, biggest loss, streaks, skew ---
    wins=[p for p in pnl if p>0]; losses=[p for p in pnl if p<0]
    avg_w=sum(wins)/len(wins); avg_l=sum(losses)/len(losses)
    payoff=avg_w/abs(avg_l)
    worst_trade=min(pnl)/NOM*100
    # max consecutive losing trades
    cl=mcl=0
    for p in pnl:
        cl=cl+1 if p<0 else 0; mcl=max(mcl,cl)
    sk = sum(((p-sum(pnl)/len(pnl)))**3 for p in pnl)/len(pnl)/(math.sqrt(sum((p-sum(pnl)/len(pnl))**2 for p in pnl)/len(pnl))**3)

    # --- Dp: durability — monthly consistency, worst month, losing-month streak ---
    posm=100*sum(1 for x in mr if x>0)/n
    worst_m=min(mr); best_m=max(mr)
    dl=mdl=0
    for x in mr:
        dl=dl+1 if x<0 else 0; mdl=max(mdl,dl)
    # year concentration: top-2 years share of total
    yr=defaultdict(float)
    for k in keys: yr[k[0]]+=m[k]
    tot=sum(yr.values()); top2=sum(sorted(yr.values(),reverse=True)[:2])
    conc=top2/tot*100 if tot else 0

    # --- Pf & VaR ---
    var95=sorted(mr)[int(0.05*n)]
    sharpe=mean/sd*math.sqrt(12)

    print("=== CatBa v1.1 — Darwinex attribute scorecard (proxies) ===\n")
    print(f"PERFORMANCE (Pf)   ann Sharpe {sharpe:.2f} | mean {mean:+.2f}%/mo | 95% monthly VaR {var95:.2f}%")
    print(f"RISK STABILITY(Ra) vol-of-vol {vol_of_vol:.2f}  (lower=steadier risk; <0.3 good, >0.5 unstable)")
    print(f"LOSS AVERSION (La) payoff(avgW/avgL) {payoff:.2f} | trade skew {sk:+.2f} | worst trade {worst_trade:.2f}% | max consec losses {mcl}")
    print(f"DURABILITY   (Dp)  positive months {posm:.0f}% | worst month {worst_m:.1f}% | longest losing-month streak {mdl}")
    print(f"                   TOP-2-YEAR concentration {conc:.0f}% of all profit  <-- the Darwinex problem")
    print()
    print("READ:")
    print(f"  STRONG: skew {sk:+.2f} (winners>losers), payoff {payoff:.2f}, worst month {worst_m:.1f}% (shallow)")
    print(f"  WEAK:   top-2-year concentration {conc:.0f}% -> durability score capped")
    print(f"          {mdl}-month losing streaks -> hurts consistency")

if __name__=="__main__":
    main()
