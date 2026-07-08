"""BREAK-EVEN OPTIMIZER model for CatBa.

Replays each historical trade's real intraday path (M5) under a grid of
break-even triggers and measures P&L. Isolates the BE effect (entries/SL/TP
held fixed at what the EA actually took; only the BE rule varies).

EA BE rule (from update_sl_to_be): once price moves beAtrMult*ATR(14,D1) in
favour, move SL to entry +/- add_pip_to_sl (a small locked profit). We sweep
beAtrMult (0 = no BE) and report P&L/win%/PF/avg-win/avg-loss per value, at a
realistic 3-pip round-trip spread.

Inputs: tradesx_ema13.csv (entry_time, side, entry, sl, tp) + smt_GBPJPY_M5.csv
(intraday path) + daily ATR from H1.
"""
import csv, datetime as dt, bisect
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
PIP=0.01; SPREAD_PIPS=3.0; ADD_LOCK=0.2   # add_pip_to_sl (EA default)

def load_m5():
    t=[]; o=[]; h=[]; l=[]; c=[]
    for r in csv.reader(open(fr"{CF}\smt_GBPJPY_M5.csv")):
        if not r or r[0]=="time": continue
        t.append(int(r[0])); h.append(float(r[2])); l.append(float(r[3]))
    return t, h, l   # epoch, high, low (enough for path replay)

def daily_atr():
    byday=defaultdict(list)
    for r in csv.reader(open(fr"{CF}\smt_GBPJPY_H1.csv")):
        if not r or r[0]=="time": continue
        tt=dt.datetime.utcfromtimestamp(int(r[0]))
        byday[tt.date()].append((float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    D=[]
    for dd in sorted(byday):
        g=byday[dd]; D.append((dd,g[0][0],max(x[1] for x in g),min(x[2] for x in g),g[-1][3]))
    n=len(D); tr=[None]*n
    for i in range(1,n):
        h,l,pc=D[i][2],D[i][3],D[i-1][4]; tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    atr=[None]*n; s=None; acc=0.0; cnt=0
    for i in range(n):
        if tr[i] is None: continue
        if s is None:
            acc+=tr[i]; cnt+=1
            if cnt==14: s=acc/14; atr[i]=s
        else: s=(s*13+tr[i])/14; atr[i]=s
    # map date -> ATR known as of PRIOR day (no look-ahead)
    out={}
    for i in range(1,n):
        if atr[i-1]: out[D[i][0]]=atr[i-1]
    return out

def load_trades():
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            et=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M")
            side=r["side"].strip().upper(); entry=float(r["entry"]); sl=float(r["sl"]); tp=float(r["tp"])
        except: continue
        rows.append((et,side,entry,sl,tp))
    return rows

def replay(t,h,l, start_idx, side, entry, sl, tp, be_dist):
    """Walk M5 bars from start_idx; apply BE once price moves be_dist in favour.
    Return exit price (pips P&L computed by caller). be_dist<=0 => no BE."""
    cur_sl=sl; moved=False; MAXBARS=8000   # ~1 month of M5
    n=len(t)
    for i in range(start_idx, min(start_idx+MAXBARS, n)):
        hi=h[i]; lo=l[i]
        # BE only valid when trigger distance exceeds the lock (else stop would be
        # set above the market -> MT5 rejects it; no impossible fills).
        if side=="BUY":
            if not moved and be_dist>ADD_LOCK and hi>=entry+be_dist:
                cur_sl=max(cur_sl, entry+ADD_LOCK); moved=True
            hit_sl = lo<=cur_sl; hit_tp = hi>=tp
            if hit_sl and hit_tp: return cur_sl   # SL-first (conservative)
            if hit_sl: return cur_sl
            if hit_tp: return tp
        else:
            if not moved and be_dist>ADD_LOCK and lo<=entry-be_dist:
                cur_sl=min(cur_sl, entry-ADD_LOCK); moved=True
            hit_sl = hi>=cur_sl; hit_tp = lo<=tp
            if hit_sl and hit_tp: return cur_sl
            if hit_sl: return cur_sl
            if hit_tp: return tp
    return None   # unresolved (rare)

def main():
    print("loading M5 path data..."); t,h,l=load_m5()
    atr=daily_atr(); trades=load_trades()
    print(f"{len(t)} M5 bars, {len(trades)} trades")
    grid=[0.0,0.1,0.2,0.3,0.4,0.5,0.7,1.0]   # 0 = no break-even
    res={g:[] for g in grid}
    for et,side,entry,sl,tp in trades:
        a=atr.get(et.date())
        if not a: continue
        si=bisect.bisect_left(t, int(et.timestamp()))
        if si>=len(t): continue
        for g in grid:
            ex=replay(t,h,l,si,side,entry,sl,tp, g*a)
            if ex is None: continue
            pips=((ex-entry) if side=="BUY" else (entry-ex))/PIP - SPREAD_PIPS
            res[g].append(pips)
    print(f"\nBE-trigger optimization (beAtrMult; 0=no BE), net of {SPREAD_PIPS}p spread:")
    print(f"{'beAtrMult':>10}{'n':>6}{'netPips':>10}{'avgPips':>9}{'win%':>7}{'PF':>7}{'avgWin':>8}{'avgLoss':>9}")
    for g in grid:
        v=res[g]
        if not v: continue
        wins=[x for x in v if x>0]; losses=[x for x in v if x<=0]
        gp=sum(wins); gl=-sum(losses)
        pf=gp/gl if gl>0 else 0
        aw=gp/len(wins) if wins else 0; al=(sum(losses)/len(losses)) if losses else 0
        tag=" <-- current" if abs(g-0.3)<1e-9 else (" (no BE)" if g==0 else "")
        print(f"{g:>10.1f}{len(v):>6}{sum(v):>10.0f}{sum(v)/len(v):>9.2f}{100*len(wins)/len(v):>6.0f}%{pf:>7.3f}{aw:>8.1f}{al:>9.1f}{tag}")

if __name__=="__main__":
    main()
