#!/bin/bash
# Widening-window grind: cache GBPJPY M1 back to 2016 in steps, saving each result.
TERM="C:/Program Files/Darwinex MetaTrader 5/terminal64.exe"
CSV="C:/Users/giaho/AppData/Roaming/MetaQuotes/Terminal/Common/Files/catba_results.csv"
BT="C:/Users/giaho/repos/mql5/catba/backtest"
mkdir -p "$BT/results"

run_one () {
  local fy=$1
  local ini="$BT/grind_${fy}.ini"
  cat > "$ini" <<INI
[Tester]
Expert=Advisors\catba\CatBa.ex5
Symbol=GBPJPY
Period=H1
Optimization=0
Model=1
FromDate=${fy}.01.02
ToDate=2026.07.03
ForwardMode=0
Deposit=1600000
Currency=JPY
Leverage=100
Visual=0
ShutdownTerminal=1
[TesterInputs]
lotSize=0.0
riskPercentPerTrade=2.0
useRiskPercentPerTrade=true
emaPeriod=8
checkEveryMinutes=12
timeFrame=H1
tradingSymbol=GBPJPY
symbolUJOnBroker=USDJPY
requiredClosedBothSideOfEMA=false
minPipsRequiredFromYesterday=0.28
minPipsRequiredFromLastWeek=0.0
addPipsToEMA=0.11
DistanceToTriggerBE=0.72
add_pip_to_sl=0.2
INI
  powershell -NoProfile -Command "Get-Process terminal64 -ErrorAction SilentlyContinue | Stop-Process -Force" >/dev/null 2>&1
  sleep 2
  rm -f "$CSV"
  INIWIN=$(cygpath -w "$ini")
  powershell -NoProfile -Command "Start-Process -FilePath '$TERM' -ArgumentList '/config:$INIWIN'" >/dev/null 2>&1
  echo "[$(date +%H:%M:%S)] launched from ${fy} ..."
  for i in $(seq 1 78); do
    if [ -f "$CSV" ]; then cp "$CSV" "$BT/results/from_${fy}.csv"; echo "  from ${fy}: OK ($(date +%H:%M:%S))"; return 0; fi
    if ! tasklist //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | grep -qi terminal64; then
       sleep 2
       if [ -f "$CSV" ]; then cp "$CSV" "$BT/results/from_${fy}.csv"; echo "  from ${fy}: OK-on-exit"; return 0; fi
       echo "  from ${fy}: exited, no CSV (download timed out this pass)"; return 1
    fi
    sleep 10
  done
  echo "  from ${fy}: watcher timeout"; return 1
}

for fy in 2024 2022 2020 2018 2016; do
  run_one $fy || echo "  (continuing; each pass still extends the cache)"
done
echo "=== GRIND DONE ==="
ls -la "$BT/results/"
