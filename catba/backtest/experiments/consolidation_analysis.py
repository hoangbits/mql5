"""Does CatBa lose INSIDE consolidation? Bucket each trade by how consolidated
GBPJPY was at entry. If losers concentrate in consolidation -> a 'skip range,
trade expansion' filter (ICT accumulation->expansion) is worth building.

Consolidation proxies at entry day (from D1 built off H1):
  - range10/ATR : 10-day (high-low) in ATR units (low = tight/consolidated)
  - ATR percentile : is current ATR low vs last 100d (low = quiet)
  - ADX(14) : for comparison with the killed H14 gate
"""
import csv, math, datetime as dt
from collections import defaultdict

H1 = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files\smt_GBPJPY_H1.csv"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"

def daily():
    d=defaultdict(list)
    for r in csv.reader(open(H1)):
        if r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        d[t.date()].append((float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    out=[]
    for dd in sorted(d):
        b=d[dd]; out.append((dd,b[0][0],max(x[1] for x in b),min(x[2] for x in b),b[-1][3]))
    return out  # date,o,h,l,c

def wilder(v,p):
    out=[None]*len(v); s=None; acc=0.0; cnt=0
    for i in range(len(v)):
        if v[i] is None: continue
        if s is None:
            acc+=v[i]; cnt+=1
            if cnt==p: s=acc/p; out[i]=s
        else:
            s=(s*(p-1)+v[i])/p; out[i]=s
    return out

def features():
    D=daily(); n=len(D); tr=[None]*n
    for i in range(1,n):
        h,l,pc=D[i][2],D[i][3],D[i-1][4]; tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    atr=wilder(tr,14)
    # ADX
    pdm=[None]*n; ndm=[None]*n
    for i in range(1,n):
        up=D[i][2]-D[i-1][2]; dn=D[i-1][3]-D[i][3]
        pdm[i]=up if(up>dn and up>0) else 0.0; ndm[i]=dn if(dn>up and dn>0) else 0.0
    spdm=wilder(pdm,14); sndm=wilder(ndm,14); dx=[None]*n
    for i in range(n):
        if atr[i] and atr[i]>0 and spdm[i] is not None:
            pdi=100*spdm[i]/atr[i]; ndi=100*sndm[i]/atr[i]; s=pdi+ndi
            dx[i]=100*abs(pdi-ndi)/s if s>0 else 0
    adx=wilder(dx,14)
    feat={}
    for i in range(11,n):
        d=D[i][0]                      # entry day
        a=atr[i-1]                     # ATR known BEFORE day i (no look-ahead)
        if not a or a<=0: continue
        rng10=max(x[2] for x in D[i-10:i])-min(x[3] for x in D[i-10:i])  # prior 10 days
        comp=rng10/a
        hist=[atr[j] for j in range(max(0,i-101),i-1) if atr[j]]
        pct=100*sum(1 for x in hist if x<a)/len(hist) if hist else 50
        feat[d]=(comp, pct, adx[i-1] if adx[i-1] else 0)
    return feat

def qbucket(rows,key,labels):
    vals=sorted(r[key] for r in rows); q=[vals[int(len(vals)*p)] for p in(0.33,0.66)]
    g=defaultdict(list)
    for r in rows:
        v=r[key]; b=labels[0] if v<=q[0] else (labels[1] if v<=q[1] else labels[2])
        g[b].append(r)
    return [(l,g[l]) for l in labels], q

def show(title,groups):
    print(f"--- {title} ---")
    for name,rows in groups:
        n=len(rows)
        if not n: continue
        w=100*sum(1 for r in rows if r['pf']>0)/n; tot=sum(r['pf'] for r in rows)
        flag="  <-- LOSS" if tot<0 else ""
        print(f"  {name:<22}{n:>5}  win {w:>4.1f}%  total {tot:>9.0f}{flag}")
    print()

def main():
    feat=features()
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            t=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M").date()
            pf=float(r["profit"])   # rich dump: already net
        except: continue
        # match feature to entry day (or nearest prior)
        f=feat.get(t)
        if not f:
            continue
        rows.append(dict(pf=pf, comp=f[0], atrpct=f[1], adx=f[2]))
    print(f"matched {len(rows)} trades to daily features\n")
    g,_=qbucket(rows,'comp',["compressed(tight)","medium","expanded(wide)"])
    show("by 10-day RANGE/ATR (tight=consolidation)", g)
    g,_=qbucket(rows,'atrpct',["lowATR(quiet)","medium","highATR(active)"])
    show("by ATR percentile (low=quiet/consolidating)", g)
    g,_=qbucket(rows,'adx',["lowADX(range)","medium","highADX(trend)"])
    show("by ADX (low=range, high=trend)", g)

if __name__=="__main__":
    main()
