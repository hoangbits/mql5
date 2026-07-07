"""Research the TIME aspect of GBPJPY trades. User hypothesis: the :00/:12/:24/
:36/:48 check grid (phase 0) is a real ADVANTAGE, not luck — esp. :00 = H1 bar
boundary (fresh EMA, institutional round-mark flow). Test which marks carry the
edge, with IS(2016-21)/OOS(2022-26) robustness, + hour-of-day and bar-boundary
angles. Trade dump entries are all phase-0 (at the 5 marks)."""
import csv, datetime as dt
from collections import defaultdict

TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"

def load():
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            et=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            side=r["side"].strip().upper(); pf=float(r["profit"]); hold=float(r["hold_min"] or 0)
        except: continue
        rows.append((et,side,pf,hold))
    return rows

def bucket(rows,key,order=None):
    g=defaultdict(lambda:[0,0,0.0,0.0,0.0])  # n,wins,net,isnet,oosnet
    for et,side,pf,hold in rows:
        k=key(et,side,hold)
        if k is None: continue
        b=g[k]; b[0]+=1; b[1]+= (1 if pf>0 else 0); b[2]+=pf
        if et.year<=2021: b[3]+=pf
        else: b[4]+=pf
    return [(k,g[k]) for k in (order or sorted(g)) if k in g]

def show(title,groups):
    print(f"--- {title} ---")
    print(f"   {'bucket':<12}{'n':>5}{'win%':>6}{'net':>10}{'IS net':>10}{'OOS net':>10}  {'robust':>9}")
    for k,b in groups:
        n,w,net,isn,oosn=b
        wp=100*w/n if n else 0
        rob="WIN-both" if isn>0 and oosn>0 else ("lose-both" if isn<0 and oosn<0 else "mixed")
        star=" *" if (k==0 or k=="00") else ""
        print(f"   {str(k)+star:<12}{n:>5}{wp:>5.0f}%{net:>10.0f}{isn:>10.0f}{oosn:>10.0f}  {rob:>9}")
    print()

def main():
    rows=load()
    print(f"{len(rows)} trades (all phase-0: entries at :00/:12/:24/:36/:48)\n")

    # exact minute-of-hour mark
    show("by MINUTE-of-hour mark (:00 = H1 bar boundary)",
         bucket(rows, lambda et,s,h: et.minute, order=[0,12,24,36,48]))

    # bar-boundary hypothesis: :00 vs the rest
    show("BAR-BOUNDARY test (:00 vs off-boundary)",
         bucket(rows, lambda et,s,h: "at :00" if et.minute==0 else "off :00",
                order=["at :00","off :00"]))

    # :00 mark split by side
    show(":00-mark by side",
         bucket(rows, lambda et,s,h: (f":00 {s}" if et.minute==0 else None)))

    # hour-of-day (server) — where in the day is the edge
    show("by ENTRY HOUR (server)",
         bucket(rows, lambda et,s,h: et.hour, order=list(range(24))))

    # :00-mark by hour: is bar-boundary edge concentrated in specific hours?
    r00=[r for r in rows if r[0].minute==0]
    show(":00-mark entries by HOUR",
         bucket(r00, lambda et,s,h: et.hour, order=list(range(24))))

if __name__=="__main__":
    main()
