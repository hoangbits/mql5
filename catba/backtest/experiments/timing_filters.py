"""Do TIME-based filters (day-of-week, week-of-month, entry hour, hold time)
robustly separate CatBa's winners from losers? DANGER: multiple testing — with
5 weekday buckets some will lose in-sample by chance. A filter only counts if a
bucket is NEGATIVE in BOTH IS (2016-21) and OOS (2022-26). Otherwise it's an
overfit mirage. Data: tradesx_ema13.csv (entry_time, exit_time, profit=net).
"""
import csv, datetime as dt
from collections import defaultdict

TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
WD = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def load():
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            et=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            xt=dt.datetime.strptime(r["exit_time"].strip(),"%Y.%m.%d %H:%M") if r.get("exit_time","").strip() else None
            pf=float(r["profit"]); hold=float(r["hold_min"]) if r.get("hold_min","").strip() else 0
        except: continue
        rows.append((et,xt,pf,hold))
    return rows

def bucketed(rows, keyfn, order=None):
    g=defaultdict(lambda:[0,0.0,0,0.0,0,0.0])  # n,net, is_n,is_net, oos_n,oos_net
    for et,xt,pf,hold in rows:
        k=keyfn(et,xt,hold)
        if k is None: continue
        b=g[k]; b[0]+=1; b[1]+=pf
        if et.year<=2021: b[2]+=1; b[3]+=pf
        else: b[4]+=1; b[5]+=pf
    keys=order if order else sorted(g)
    return [(k,g[k]) for k in keys if k in g]

def show(title, groups):
    print(f"--- {title} ---")
    print(f"   {'bucket':<10}{'n':>5}{'net':>10}{'avg':>8}  {'IS net':>10}{'OOS net':>10}  robust?")
    for k,b in groups:
        n,net,isn,isnet,oosn,oosnet=b
        avg=net/n if n else 0
        rob = "LOSE-both" if (isnet<0 and oosnet<0) else ("win-both" if isnet>0 and oosnet>0 else "mixed")
        flag = "  <-- candidate" if rob=="LOSE-both" else ""
        print(f"   {str(k):<10}{n:>5}{net:>10.0f}{avg:>8.0f}  {isnet:>10.0f}{oosnet:>10.0f}  {rob}{flag}")
    print()

def main():
    rows=load()
    tot=sum(r[2] for r in rows)
    print(f"{len(rows)} trades, total net {tot:.0f}\n")

    show("DAY OF WEEK (entry)",
         bucketed(rows, lambda et,xt,h: WD[et.weekday()], order=WD))

    def wom(et):  # week-of-month 1..5 by calendar day
        return (et.day-1)//7 + 1
    show("WEEK OF MONTH (entry)",
         bucketed(rows, lambda et,xt,h: f"W{wom(et)}", order=[f"W{i}" for i in range(1,6)]))

    def hourband(h):
        return {0:"00-03",1:"00-03",2:"00-03",3:"00-03",4:"04-07",5:"04-07",6:"04-07",7:"04-07",
                8:"08-11",9:"08-11",10:"08-11",11:"08-11",12:"12-15",13:"12-15",14:"12-15",15:"12-15",
                16:"16-19",17:"16-19",18:"16-19",19:"16-19"}.get(h,"20-23")
    show("ENTRY HOUR band (server)",
         bucketed(rows, lambda et,xt,h: hourband(et.hour),
                  order=["00-03","04-07","08-11","12-15","16-19","20-23"]))

    show("DAY x nothing: HOLD time band",
         bucketed(rows, lambda et,xt,h: ("<2h" if h<120 else "2-8h" if h<480 else "8-24h" if h<1440 else ">1d"),
                  order=["<2h","2-8h","8-24h",">1d"]))

    # combo: weekday that loses in both halves — how much would skipping it save?
    print("=== if we SKIP any 'LOSE-both' weekday, net effect (IS/OOS) ===")
    dow=bucketed(rows, lambda et,xt,h: WD[et.weekday()], order=WD)
    for k,b in dow:
        n,net,isn,isnet,oosn,oosnet=b
        if isnet<0 and oosnet<0:
            print(f"   skip {k}: recover IS {-isnet:.0f} + OOS {-oosnet:.0f} = {-net:.0f} over {n} trades")
    if not any(b[3]<0 and b[5]<0 for _,b in dow):
        print("   (no weekday loses in BOTH halves -> no robust day-of-week filter)")

if __name__=="__main__":
    main()
