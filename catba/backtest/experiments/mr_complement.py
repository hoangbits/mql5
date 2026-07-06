"""Second GBPJPY edge to COMPLEMENT CatBa: a mean-reversion (z-score fade) that
trades exactly where CatBa bleeds — LOW-vol chop / reversals. The durability
fix has to come from a 2nd UNCORRELATED edge, not more tuning of CatBa.

Design (pre-registered, economically grounded):
  signal at close of day i (no leak): z = (close - SMA20)/STD20.
  If z <= -Z -> price stretched DOWN -> fade LONG day i+1.
  If z >= +Z -> stretched UP -> fade SHORT day i+1.
  CONDITION on regime via ATR-percentile (trailing 252d): test the fade in
  LOW / MID / HIGH vol separately — hypothesis: MR works in LOW vol (CatBa's
  weak spot), trend-following (CatBa) works in HIGH vol. Complementary.
  Proxy P&L = direction*(close[i+1]-open[i+1]) in pips (1-day hold, no stop).

Verdict bar (honest): a candidate is worth building only if
  (a) standalone OOS edge > 0 (not just IS), AND
  (b) low/negative correlation to CatBa monthly returns, AND
  (c) the CatBa+MR combo improves durability (green years, worst month).
MR on GBPJPY already failed once (turtle-soup twin). If it fails again -> MR
is not the answer; say so.
"""
import csv, math, datetime as dt
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
PIP=0.01; NOM=1_600_000

def daily():
    d=defaultdict(list)
    for r in csv.reader(open(fr"{CF}\smt_GBPJPY_H1.csv")):
        if not r or r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        d[t.date()].append((float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    return [(dd,b[0][0],max(x[1] for x in b),min(x[2] for x in b),b[-1][3])
            for dd in sorted(d) for b in [d[dd]]]

def wilder(v,p):
    out=[None]*len(v); s=None; acc=0.0; cnt=0
    for i in range(len(v)):
        if v[i] is None: continue
        if s is None:
            acc+=v[i]; cnt+=1
            if cnt==p: s=acc/p; out[i]=s
        else: s=(s*(p-1)+v[i])/p; out[i]=s
    return out

def mr_signals(Z):
    """Return list of (date_of_trade, pnl_pips, atr_pct_at_signal) for the MR
    fade. Signal at close of i (uses SMA/STD up to i), trade i+1 open->close."""
    D=daily(); n=len(D); c=[x[4] for x in D]
    tr=[None]*n
    for i in range(1,n):
        h,l,pc=D[i][2],D[i][3],D[i-1][4]; tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    atr=wilder(tr,14)
    out=[]
    for i in range(20,n-1):
        w=c[i-20:i]; mu=sum(w)/20; sd=math.sqrt(sum((x-mu)**2 for x in w)/19)
        if sd<=0: continue
        z=(c[i]-mu)/sd
        a=atr[i]
        if not a: continue
        hist=[atr[j] for j in range(max(0,i-252),i) if atr[j]]
        pct=100*sum(1 for x in hist if x<a)/len(hist) if hist else 50
        direction=0
        if z<=-Z: direction=+1
        elif z>=Z: direction=-1
        if not direction: continue
        o1=D[i+1][1]; c1=D[i+1][4]; d1=D[i+1][0]
        pnl=direction*(c1-o1)/PIP
        out.append((d1,pnl,pct))
    return out

def catba_monthly():
    m=defaultdict(float)
    for r in csv.DictReader(open(TR)):
        try:
            t=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            m[(t.year,t.month)]+=float(r["profit"])
        except: continue
    return m

def sharpe(vals):
    if len(vals)<3: return 0.0
    mu=sum(vals)/len(vals); sd=math.sqrt(sum((x-mu)**2 for x in vals)/(len(vals)-1))
    return mu/sd*math.sqrt(12) if sd else 0.0

def main():
    print("=== MR fade standalone edge by vol regime (Z=1.0) ===")
    print("(if MR is real & complementary: profitable in LOW vol, OOS>0)\n")
    for Z in (1.0,1.5):
        sig=mr_signals(Z)
        print(f"-- Z={Z}  ({len(sig)} fade days) --")
        for lo,hi,name in [(0,33,'LOW vol'),(33,66,'MID vol'),(66,100,'HIGH vol')]:
            band=[(d,p) for d,p,pct in sig if lo<=pct<hi]
            is_=[p for d,p in band if d.year<=2021]; oos=[p for d,p in band if d.year>2021]
            tot=sum(p for _,p in band); wr=100*sum(1 for _,p in band if p>0)/len(band) if band else 0
            print(f"   {name:<9} {len(band):>4}d  net {tot:>+8.0f}p  win {wr:>4.1f}%  "
                  f"IS {sum(is_):>+7.0f}p  OOS {sum(oos):>+7.0f}p")
        print()

    # best complementary variant: LOW-vol fade, Z=1.0 -> monthly series
    sig=mr_signals(1.0)
    mr_m=defaultdict(float)
    for d,p,pct in sig:
        if pct<33: mr_m[(d.year,d.month)]+=p        # low-vol fade only
    cb=catba_monthly()
    keys=sorted(set(cb)|set(mr_m))
    cbv=[cb.get(k,0)/NOM*100 for k in keys]          # CatBa monthly return %
    # scale MR pips to comparable risk (unit vol), express both as % of vol
    mrv=[mr_m.get(k,0) for k in keys]
    n=len(keys); mc=sum(cbv)/n; mm=sum(mrv)/n
    sc=math.sqrt(sum((v-mc)**2 for v in cbv)/n) or 1
    sm=math.sqrt(sum((v-mm)**2 for v in mrv)/n) or 1
    corr=sum((cbv[i]-mc)*(mrv[i]-mm) for i in range(n))/n/(sc*sm)
    print(f"=== LOW-vol MR fade vs CatBa (monthly) ===")
    print(f"correlation = {corr:+.2f}   (want <=0 for a hedge)")
    print(f"MR standalone monthly Sharpe = {sharpe(mrv):.2f}  "
          f"(IS {sharpe([mrv[i] for i in range(n) if keys[i][0]<=2021]):.2f} / "
          f"OOS {sharpe([mrv[i] for i in range(n) if keys[i][0]>2021]):.2f})\n")

    # combined durability (equal-risk normalized), sweep weights
    cbn=[v/sc for v in cbv]; mrn=[v/sm for v in mrv]
    print(f"{'wCatBa/wMR':>11}{'Sharpe':>8}{'greenYr':>9}{'worstMo':>9}")
    for w in (1.0,0.8,0.7,0.6,0.5):
        port=[w*cbn[i]+(1-w)*mrn[i] for i in range(n)]
        yr=defaultdict(float)
        for i,k in enumerate(keys): yr[k[0]]+=port[i]
        gy=sum(1 for v in yr.values() if v>0)
        print(f"{int(w*100):>4}/{int((1-w)*100):<6}{sharpe(port):>8.2f}{gy:>6}/{len(yr)}"
              f"{min(port):>9.2f}")
    print("\n(w=100/0 = CatBa alone. Improvement = higher Sharpe AND more green"
          " years AND shallower worst month.)")

if __name__=="__main__":
    main()
