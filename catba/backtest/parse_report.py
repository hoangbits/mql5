"""Parse an MT5 Strategy Tester HTML report -> summary + per-year net profit.
Usage: python parse_report.py <report.htm>
Robust to MT5's table layout: finds the Deals table (has Time+Profit+Balance),
buckets realized profit by year."""
import sys, re
from html.parser import HTMLParser
from collections import defaultdict
import datetime as dt

class T(HTMLParser):
    def __init__(s):
        super().__init__(); s.tables=[]; s.cur=None; s.row=None; s.cell=None
    def handle_starttag(s,t,a):
        if t=="table": s.cur=[]
        elif t=="tr" and s.cur is not None: s.row=[]
        elif t in ("td","th") and s.row is not None: s.cell=""
    def handle_data(s,d):
        if s.cell is not None: s.cell+=d
    def handle_endtag(s,t):
        if t in ("td","th") and s.cell is not None:
            s.row.append(s.cell.strip()); s.cell=None
        elif t=="tr" and s.row is not None:
            s.cur.append(s.row); s.row=None
        elif t=="table" and s.cur is not None:
            s.tables.append(s.cur); s.cur=None

def num(x):
    x=x.replace(" ","").replace(" ","").replace(",","")
    try: return float(x)
    except: return None

def parse(path):
    html=open(path,encoding="utf-8",errors="replace").read()
    p=T(); p.feed(html)
    # summary key/values (flatten all 2-col rows)
    summ={}
    for tbl in p.tables:
        for r in tbl:
            for i in range(len(r)-1):
                k=r[i].rstrip(":").strip()
                if k in ("Total Net Profit","Profit Factor","Total Trades","Expected Payoff",
                         "Balance Drawdown Maximal","Sharpe Ratio","Recovery Factor",
                         "Gross Profit","Gross Loss","LR Correlation","Short Trades (won %)",
                         "Long Trades (won %)","Maximal drawdown"):
                    summ.setdefault(k, r[i+1].strip())
    # find deals table: header row containing Time & Profit & Balance
    deals=None; hdr=None
    for tbl in p.tables:
        for ri,r in enumerate(tbl):
            low=[c.lower() for c in r]
            if "time" in low and "profit" in low and "balance" in low:
                hdr=r; deals=tbl[ri+1:];
                ti=low.index("time"); pi=low.index("profit"); bi=low.index("balance")
                break
        if deals is not None: break
    per_year=defaultdict(float); per_year_n=defaultdict(int); rows=0
    if deals:
        for r in deals:
            if len(r)<=max(ti,pi,bi): continue
            m=re.match(r"(\d{4})\.(\d{2})\.(\d{2})", r[ti])
            if not m: continue
            prof=num(r[pi]); bal=num(r[bi])
            if prof is None or bal is None: continue   # only realized 'out' deals have both
            yr=int(m.group(1)); per_year[yr]+=prof; per_year_n[yr]+=1; rows+=1
    return summ, per_year, per_year_n, rows

if __name__=="__main__":
    summ,py,pyn,rows=parse(sys.argv[1])
    print("=== SUMMARY ===")
    for k,v in summ.items(): print(f"  {k}: {v}")
    print(f"\n=== PER-YEAR (from {rows} closed deals) ===")
    print(f"{'Year':>6} {'Trades':>7} {'NetProfit':>12}")
    cum=0
    for y in sorted(py):
        cum+=py[y]
        flag="" if py[y]>=0 else "  <-- NEGATIVE"
        print(f"{y:>6} {pyn[y]:>7} {py[y]:>12,.2f}{flag}")
    print(f"\nSum of per-year net: {sum(py.values()):,.2f}")
    neg=[y for y in py if py[y]<0]
    print("Negative years:", neg if neg else "NONE")
