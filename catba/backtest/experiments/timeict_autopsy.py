"""Losing-trade autopsy via TIME + ICT features (GBPJPY). Goal: do losers
concentrate in identifiable ICT/time buckets we can filter WITHOUT killing
winners? Discipline: a bucket only counts if it loses in BOTH IS (2016-21) and
OOS (2022-26). Multiple-testing is severe here — treat single-half signals as
noise. Context: phase-fragility suggests win/loss is knife-edge, so expect
weak separability.

Features per trade at entry (no look-ahead; uses H1 bars strictly before entry):
  A) ICT premium/discount: pos = (entry - yLow)/(yHigh-yLow) in YESTERDAY's D1
     range. ICT: buy DISCOUNT(<0.5), sell PREMIUM(>0.5). 'counter' = buy premium
     / sell discount (theory: worse).
  B) Liquidity sweep before entry: did entry-day H1 (before entry) sweep
     yesterday's high (buyside) or low (sellside)? ICT: buy AFTER a sellside
     sweep, sell AFTER a buyside sweep. 'aligned' = swept the side you're fading.
  C) Killzone of entry (server hrs): London 8-12, NY 13-17, Asian 0-7, else.
"""
import csv, datetime as dt
from collections import defaultdict

H1 = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files\smt_GBPJPY_H1.csv"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"

def load_h1():
    bars=[]
    for r in csv.reader(open(H1)):
        if not r or r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        bars.append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    return bars

def build():
    bars=load_h1()
    byday=defaultdict(list)
    for b in bars: byday[b[0].date()].append(b)
    d1={}
    for dd in byday:
        g=byday[dd]; d1[dd]=(g[0][1],max(x[2] for x in g),min(x[3] for x in g),g[-1][4])
    return bars, byday, d1

def load_trades():
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            et=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            side=r["side"].strip().upper(); entry=float(r["entry"]); pf=float(r["profit"])
        except: continue
        rows.append((et,side,entry,pf))
    return rows

def features(rows, byday, d1):
    dates=sorted(d1)
    di={dd:i for i,dd in enumerate(dates)}
    out=[]
    for et,side,entry,pf in rows:
        dd=et.date()
        if dd not in di or di[dd]==0: continue
        yo,yh,yl,yc=d1[dates[di[dd]-1]]        # yesterday D1
        rng=yh-yl
        if rng<=0: continue
        pos=(entry-yl)/rng                       # 0=at yLow,1=at yHigh
        # ICT premium/discount alignment
        if side=="BUY":  disc_aligned = pos<=0.5
        else:            disc_aligned = pos>=0.5
        # liquidity sweep before entry (entry-day H1 bars strictly before et)
        swHigh=swLow=False
        for b in byday.get(dd,[]):
            if b[0]>=et: break
            if b[2]>yh: swHigh=True
            if b[3]<yl: swLow=True
        if side=="BUY":  sweep_aligned = swLow
        else:            sweep_aligned = swHigh
        h=et.hour
        kz = "London" if 8<=h<12 else ("NY" if 13<=h<17 else ("Asian" if h<8 else "other"))
        out.append(dict(et=et,side=side,pf=pf,pos=pos,disc=disc_aligned,
                        sweep=sweep_aligned,kz=kz))
    return out

def report(feat, key, labels):
    print(f"--- by {key} ---")
    g=defaultdict(lambda:[0,0.0,0.0,0.0,0,0])  # n,net,isnet,oosnet,isW,oosW... simplify
    agg=defaultdict(lambda:[0,0.0,0,0.0,0,0.0])  # n,net, is_n,is_net, oos_n,oos_net
    win=defaultdict(lambda:[0,0])  # wins, n
    for r in feat:
        k=r[key]; a=agg[k]; a[0]+=1; a[1]+=r['pf']
        if r['et'].year<=2021: a[2]+=1; a[3]+=r['pf']
        else: a[4]+=1; a[5]+=r['pf']
        win[k][1]+=1; win[k][0]+= (1 if r['pf']>0 else 0)
    print(f"   {'bucket':<14}{'n':>5}{'win%':>6}{'net':>10}{'IS net':>10}{'OOS net':>10}  robust")
    for k in (labels or sorted(agg)):
        if k not in agg: continue
        n,net,isn,isnet,oosn,oosnet=agg[k]
        w=100*win[k][0]/win[k][1] if win[k][1] else 0
        rob="LOSE-both" if isnet<0 and oosnet<0 else ("win-both" if isnet>0 and oosnet>0 else "mixed")
        print(f"   {str(k):<14}{n:>5}{w:>5.0f}%{net:>10.0f}{isnet:>10.0f}{oosnet:>10.0f}  {rob}")
    print()

def main():
    bars,byday,d1=build()
    rows=load_trades()
    feat=features(rows,byday,d1)
    tot=sum(r['pf'] for r in feat)
    print(f"{len(feat)} trades matched to ICT features; total net {tot:.0f}\n")

    report(feat,'disc',[True,False])   # premium/discount aligned
    report(feat,'sweep',[True,False])  # liquidity-sweep aligned
    report(feat,'kz',["Asian","London","NY","other"])

    # ICT-bad = counter premium/discount AND no favorable sweep
    for r in feat: r['ictbad'] = (not r['disc']) and (not r['sweep'])
    report(feat,'ictbad',[True,False])

    # if we SKIP ictbad, what happens (keep winners?)
    keep=[r for r in feat if not r['ictbad']]; skip=[r for r in feat if r['ictbad']]
    def stats(s):
        n=len(s); net=sum(r['pf'] for r in s); w=100*sum(1 for r in s if r['pf']>0)/n if n else 0
        isn=sum(r['pf'] for r in s if r['et'].year<=2021); oosn=sum(r['pf'] for r in s if r['et'].year>2021)
        return n,net,w,isn,oosn
    print("=== SKIP 'ICT-bad' (counter P/D + no favorable sweep) ===")
    for tag,s in [("ALL",feat),("KEEP",keep),("SKIPPED",skip)]:
        n,net,w,isn,oosn=stats(s)
        print(f"   {tag:<8}{n:>5} trades  win {w:>4.0f}%  net {net:>9.0f}  (IS {isn:>8.0f} / OOS {oosn:>8.0f})")

if __name__=="__main__":
    main()
