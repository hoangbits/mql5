//+------------------------------------------------------------------+
//| ExportSMT.mq5 - dump aligned OHLC for GBPJPY/GBPUSD/USDJPY on     |
//| M15 & H1 to Common\Files, run inside the Strategy Tester (which   |
//| auto-downloads the partner symbols). For the SMT event study.     |
//+------------------------------------------------------------------+
#property copyright "Hoang Le"
#property version   "1.00"

string          Syms[3]    = {"GBPJPY","GBPUSD","USDJPY"};
ENUM_TIMEFRAMES Tfs[2]     = {PERIOD_M15, PERIOD_H1};
string          TfNames[2] = {"M15","H1"};

int OnInit()
  {
   for(int i=0; i<3; i++)
     {
      SymbolSelect(Syms[i], true);
      MqlRates r[];
      // touch each symbol/TF to trigger the tester's history sync
      CopyRates(Syms[i], PERIOD_M15, 0, 50, r);
      CopyRates(Syms[i], PERIOD_H1,  0, 50, r);
     }
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
   // keep partner symbols referenced so the tester keeps them synced
   double a = SymbolInfoDouble("GBPUSD", SYMBOL_BID);
   double b = SymbolInfoDouble("USDJPY", SYMBOL_BID);
  }

void export_one(string sym, ENUM_TIMEFRAMES tf, string tfname)
  {
   MqlRates r[];
   ArraySetAsSeries(r, false);
   datetime from = D'2016.01.01 00:00';
   datetime to   = TimeCurrent();
   int n = CopyRates(sym, tf, from, to, r);
   if(n <= 0)
     {
      PrintFormat("ExportSMT: %s %s NO DATA err=%d", sym, tfname, GetLastError());
      return;
     }
   string fn = "smt_" + sym + "_" + tfname + ".csv";
   int h = FileOpen(fn, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(h == INVALID_HANDLE)
     {
      PrintFormat("ExportSMT: open fail %s err=%d", fn, GetLastError());
      return;
     }
   FileWrite(h, "time", "open", "high", "low", "close", "tickvol");
   for(int i=0; i<n; i++)
      FileWrite(h, (long)r[i].time, r[i].open, r[i].high, r[i].low, r[i].close, (long)r[i].tick_volume);
   FileClose(h);
   PrintFormat("ExportSMT: %s %s exported %d bars (%s..%s)",
               sym, tfname, n,
               TimeToString(r[0].time, TIME_DATE),
               TimeToString(r[n-1].time, TIME_DATE));
  }

double OnTester()
  {
   for(int i=0; i<3; i++)
      for(int j=0; j<2; j++)
         export_one(Syms[i], Tfs[j], TfNames[j]);
   return 0.0;
  }
