"""H16 — does divergence-CONFIRMED continuation beat plain continuation?

Daily bias = sign(prior D1 body). Divergence continuation-direction at the
London open (server h9-12): method A (GBPJPY makes window extreme its
partner GBPUSD fails to confirm -> relative strength that way) and method C
(sign of residual of GBPJPY window return on GBPUSD+USDJPY window returns).
Bucket each bias-day: CONFIRM (div dir == bias) / CONTRADICT (opp) / and
PLAIN = all bias-days (baseline). Metric: bias * (today D1 open->close) in
pips, win%, per year. If CONFIRM ~ PLAIN the filter is redundant.
"""
import csv, datetime as dt, numpy as np
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
WIN = range(9, 12); PIP = 0.01; TF = "H1"; RESID_THR = 0.10

def load(sym, tf):
    out = []
    with open(f"{CF}\\smt_{sym}_{tf}.csv") as f:
        r = csv.reader(f); next(r)
        for row in r:
            if len(row) < 5: continue
            out.append((int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4])))
    out.sort(); return out

def by_day(bars):
    d = defaultdict(list)
    for b in bars: d[dt.datetime.utcfromtimestamp(b[0]).date()].append(b)
    return d

def win(bars_day):
    w = [b for b in bars_day if dt.datetime.utcfromtimestamp(b[0]).hour in WIN]
    if len(w) < 3: return None
    return dict(o=w[0][1], c=w[-1][4], hi=max(b[2] for b in w), lo=min(b[3] for b in w),
                ret=w[-1][4]-w[0][1],
                mk_high=w[-1][2] >= max(b[2] for b in w)-1e-12,
                mk_low=w[-1][3] <= min(b[3] for b in w)+1e-12)

def report(name, rows):
    by = defaultdict(lambda: [0,0,0.0])
    for y,h,m in rows:
        s=by[y]; s[0]+=1; s[1]+=h; s[2]+=m
    tn=th=0; tm=0.0; neg=[]
    for y in sorted(by):
        n,h,m=by[y]; tn+=n; th+=h; tm+=m
        if m<0: neg.append(y)
    if tn==0: print(f"  {name}: no days"); return
    print(f"  {name:<28} n={tn:>4}  win={100*th/tn:>4.1f}%  avg={tm/tn/PIP:>+5.1f} pips  neg_yrs={neg}")

def main():
    gj=by_day(load("GBPJPY",TF)); gu=by_day(load("GBPUSD",TF)); uj=by_day(load("USDJPY",TF))
    days=sorted(set(gj)&set(gu)&set(uj))
    gj_daily={}
    for d in gj:
        bs=sorted(gj[d]); gj_daily[d]=(bs[0][1], bs[-1][4])   # (day open, day close)
    ordered=sorted(gj_daily); idx={d:i for i,d in enumerate(ordered)}

    # residual OLS on window returns
    recs=[]
    for d in days:
        a=win(gj[d]); b=win(gu[d]); c=win(uj[d])
        if a and b and c: recs.append((d,a,b,c))
    X=np.array([[b['ret'],c['ret']] for _,_,b,c in recs]); y=np.array([a['ret'] for _,a,_,_ in recs])
    beta,*_=np.linalg.lstsq(np.column_stack([np.ones(len(X)),X]),y,rcond=None)

    HZ=3  # forward horizon in days measured FROM WINDOW END (0=rest of today)
    plain=[]; confA=[]; contA=[]; confC=[]; contC=[]
    for d,a,b,c in recs:
        i=idx.get(d)
        if i is None or i<1 or i+HZ>=len(ordered): continue
        pd=ordered[i-1]
        po,pc=gj_daily[pd]
        body=pc-po
        if body==0: continue
        bias=1 if body>0 else -1
        fwd_close=gj_daily[ordered[i+HZ]][1]   # close HZ days ahead
        move=bias*(fwd_close - a['c'])         # forward payoff FROM WINDOW END (no leak)
        plain.append((d.year, 1 if move>0 else 0, move))
        # method A continuation direction
        dirA=0
        if a['mk_high'] and not b['mk_high']: dirA=1
        elif a['mk_low'] and not b['mk_low']: dirA=-1
        if dirA!=0:
            (confA if dirA==bias else contA).append((d.year,1 if move>0 else 0,move))
        # method C continuation direction = sign(residual)
        resid=a['ret']-(beta[0]+beta[1]*b['ret']+beta[2]*c['ret'])
        dirC=1 if resid>RESID_THR else (-1 if resid<-RESID_THR else 0)
        if dirC!=0:
            (confC if dirC==bias else contC).append((d.year,1 if move>0 else 0,move))

    print(f"H16 divergence-confirmed continuation (TF={TF}); baseline = PLAIN\n")
    report("PLAIN (all bias days)", plain)
    print("  --- method A (vs GBPUSD) ---")
    report("A CONFIRM (div==bias)", confA)
    report("A CONTRADICT (div!=bias)", contA)
    print("  --- method C (residual) ---")
    report("C CONFIRM (resid dir==bias)", confC)
    report("C CONTRADICT", contC)

if __name__=="__main__":
    main()
