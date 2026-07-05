"""H17 analysis — walk-forward + PBO/CSCV on the 36-config core-param grid.

Reads results/opt/opt_e<ema>_a<addpip>_m<minbody>.csv (each has OnTester
per-year net). Builds a config x year matrix, then:
  1. IS (2016-2022) ranking -> in-sample winner.
  2. ONE out-of-sample look (2023-2026): does the IS winner beat the current
     default (8/0.11/0.28) OOS? (the honest walk-forward test)
  3. CSCV Probability of Backtest Overfitting across annual blocks
     (Bailey/Lopez de Prado): fraction of IS/OOS splits where the IS-best
     config lands below the OOS median. PBO>~0.5 => the search is overfit.
"""
import csv, os, re, itertools, math
from statistics import median

OPT = r"C:\Users\giaho\repos\mql5\catba\backtest\results\opt"
IS_YEARS = range(2016, 2023)      # 2016-2022
OOS_YEARS = range(2023, 2027)     # 2023-2026
DEFAULT = (8, 0.11, 0.28)

def load():
    cfgs = {}
    for f in os.listdir(OPT):
        m = re.match(r"opt_e(\d+)_a([\d.]+)_m([\d.]+)\.csv", f)
        if not m: continue
        key = (int(m.group(1)), float(m.group(2)), float(m.group(3)))
        yr = {}
        iny = False
        for row in csv.reader(open(os.path.join(OPT, f))):
            if not row: continue
            if row[0] == "YEARS": iny = True; continue
            if iny and len(row) >= 2:
                try: yr[int(row[0])] = float(row[1])
                except: pass
        if yr: cfgs[key] = yr
    return cfgs

def net(yr, years): return sum(yr.get(y, 0) for y in years)

def main():
    cfgs = load()
    print(f"loaded {len(cfgs)}/36 configs\n")
    if len(cfgs) < 30:
        print("too few configs; grid may be incomplete"); return
    keys = list(cfgs)
    allyears = sorted({y for yr in cfgs.values() for y in yr})

    # 1. IS ranking
    is_rank = sorted(keys, key=lambda k: net(cfgs[k], IS_YEARS), reverse=True)
    is_win = is_rank[0]
    print("=== IN-SAMPLE (2016-2022) top 5 ===")
    for k in is_rank[:5]:
        print(f"  ema={k[0]:>2} addpip={k[1]:.2f} minbody={k[2]:.2f}  "
              f"IS={net(cfgs[k],IS_YEARS)/16000:>+6.1f}%  OOS={net(cfgs[k],OOS_YEARS)/16000:>+6.1f}%")
    print(f"  (default 8/0.11/0.28: IS={net(cfgs[DEFAULT],IS_YEARS)/16000:+.1f}%  "
          f"OOS={net(cfgs[DEFAULT],OOS_YEARS)/16000:+.1f}%)\n")

    # 2. walk-forward: IS winner's OOS vs default OOS
    oos_rank = sorted(keys, key=lambda k: net(cfgs[k], OOS_YEARS), reverse=True)
    win_oos = net(cfgs[is_win], OOS_YEARS)/16000
    def_oos = net(cfgs[DEFAULT], OOS_YEARS)/16000
    is_win_oos_rank = oos_rank.index(is_win)+1
    print("=== WALK-FORWARD (one OOS look) ===")
    print(f"  IS winner = ema={is_win[0]} addpip={is_win[1]} minbody={is_win[2]}")
    print(f"    OOS = {win_oos:+.1f}%  (rank {is_win_oos_rank}/{len(keys)} OOS)")
    print(f"  Default   OOS = {def_oos:+.1f}%")
    print(f"  -> IS winner {'BEATS' if win_oos>def_oos else 'does NOT beat'} default OOS\n")

    # 3. CSCV PBO across annual blocks (use even # of years)
    yrs = [y for y in allyears if y <= 2025]      # 10 full years
    S = len(yrs)
    half = S//2
    logits = []
    for combo in itertools.combinations(range(S), half):
        isset = [yrs[i] for i in combo]
        ooset = [yrs[i] for i in range(S) if i not in combo]
        is_perf = {k: net(cfgs[k], isset) for k in keys}
        oos_perf = {k: net(cfgs[k], ooset) for k in keys}
        best = max(keys, key=lambda k: is_perf[k])
        # OOS relative rank of the IS-best (0..1); 1=best OOS
        order = sorted(keys, key=lambda k: oos_perf[k])
        r = (order.index(best)+1)/(len(keys)+1)
        r = min(max(r, 1e-6), 1-1e-6)
        logits.append(math.log(r/(1-r)))
    pbo = sum(1 for l in logits if l <= 0)/len(logits)
    print("=== PBO / CSCV ===")
    print(f"  splits evaluated: {len(logits)}  (S={S} annual blocks)")
    print(f"  PBO = {pbo*100:.1f}%   (prob the in-sample optimum is below OOS median)")
    print(f"  -> {'OVERFIT (>50%): optimization finds noise' if pbo>0.5 else 'acceptable (<50%)'}")

if __name__ == "__main__":
    main()
