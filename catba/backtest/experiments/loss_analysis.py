"""Loss-mode analysis of the CatBa ema=13 config — find patterns in losers.

Reads tradesx_ema13.csv (entry/exit paired, side, sl, tp, reason, hold).
Slices win%/avg-P&L/total by many dimensions to find where losses concentrate
(candidate FILTERS). Any pattern found is IN-SAMPLE; must be walk-forward-
validated before adoption (this is discovery, not confirmation).
"""
import csv, datetime as dt
from collections import defaultdict

F = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
PIP = 0.01
DOW = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
REASON = {4:"SL(stop)", 5:"TP(target)"}

def load():
    ts=[]
    for r in csv.DictReader(open(F)):
        try:
            et=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            entry=float(r["entry"]); ex=float(r["exit"]); sl=float(r["sl"]); tp=float(r["tp"])
            pf=float(r["profit"]); rsn=int(r["reason"]); hold=int(r["hold_min"])
        except Exception: continue
        sl_p=abs(entry-sl)/PIP if sl>0 else 0
        tp_p=abs(tp-entry)/PIP if tp>0 else 0
        ts.append(dict(et=et, side=r["side"].strip(), pf=pf, rsn=rsn, hold=hold,
                       sl_p=sl_p, tp_p=tp_p, rr=(tp_p/sl_p if sl_p>0 else 0),
                       year=et.year, dow=et.weekday(), hour=et.hour, win=pf>0))
    return ts

def show(title, groups):
    print(f"--- {title} ---")
    print(f"  {'bucket':<18}{'n':>5}{'win%':>7}{'avg':>9}{'total':>11}")
    for name,rows in groups:
        n=len(rows)
        if n==0: print(f"  {name:<18}{0:>5}"); continue
        w=100*sum(1 for r in rows if r['win'])/n
        tot=sum(r['pf'] for r in rows); avg=tot/n
        flag="  <-- LOSS" if tot<0 else ""
        print(f"  {name:<18}{n:>5}{w:>6.1f}%{avg:>9.0f}{tot:>11.0f}{flag}")
    print()

def quartiles(ts, key):
    vals=sorted(r[key] for r in ts)
    q=[vals[int(len(vals)*p)] for p in (0.25,0.5,0.75)]
    def b(v):
        if v<=q[0]: return f"Q1 <={q[0]:.0f}"
        if v<=q[1]: return f"Q2 <={q[1]:.0f}"
        if v<=q[2]: return f"Q3 <={q[2]:.0f}"
        return f"Q4 >{q[2]:.0f}"
    g=defaultdict(list)
    for r in ts: g[b(r[key])].append(r)
    return sorted(g.items())

def main():
    ts=load()
    tot=sum(r['pf'] for r in ts)
    print(f"trades={len(ts)}  win%={100*sum(1 for r in ts if r['win'])/len(ts):.1f}  net={tot:,.0f} JPY\n")

    show("by EXIT REASON", sorted(
        [(REASON.get(k,f"other({k})"), [r for r in ts if r['rsn']==k]) for k in set(r['rsn'] for r in ts)],
        key=lambda x:-len(x[1])))
    show("by SIDE", [(s,[r for r in ts if r['side']==s]) for s in ("buy","sell")])
    show("by SL distance (pips)", quartiles(ts,'sl_p'))
    show("by TP distance (pips)", quartiles(ts,'tp_p'))
    show("by R:R (tp/sl)", quartiles(ts,'rr'))
    show("by HOLD time (min)", quartiles(ts,'hold'))
    show("by DAY OF WEEK", [(DOW[d],[r for r in ts if r['dow']==d]) for d in range(5)])
    hb=[("h0-8",range(0,9)),("h9-11",range(9,12)),("h12-16",range(12,17)),("h17-23",range(17,24))]
    show("by ENTRY HOUR (server)", [(nm,[r for r in ts if r['hour'] in hh]) for nm,hh in hb])
    show("by YEAR", [(str(y),[r for r in ts if r['year']==y]) for y in sorted(set(r['year'] for r in ts))])

if __name__=="__main__":
    main()
