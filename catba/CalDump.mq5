//+------------------------------------------------------------------+
//| CalDump.mq5 — dump high(red)+moderate(orange) impact GBP/JPY/USD  |
//| economic-calendar events to Common\Files\calendar_dump.csv.       |
//| Tests whether CalendarValueHistory() is reachable in the tester.  |
//| Runs the full-range query in OnInit so the tester period can be   |
//| tiny (fast) while the dump still covers 2016..now.                |
//+------------------------------------------------------------------+
#property copyright "Hoang Le"
#property version   "1.00"

int OnInit()
  {
   int fh = FileOpen("calendar_dump.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh==INVALID_HANDLE) { Print("CalDump: cannot open file"); return(INIT_FAILED); }
   FileWrite(fh, "time","currency","importance","event");

   datetime from = D'2016.01.01 00:00';
   datetime to   = D'2026.07.03 00:00';
   string ccys[] = {"GBP","JPY","USD"};
   int total=0, raw=0;

   for(int c=0; c<ArraySize(ccys); c++)
     {
      MqlCalendarValue values[];
      int n = CalendarValueHistory(values, from, to, NULL, ccys[c]);
      raw += n;
      for(int i=0; i<n; i++)
        {
         MqlCalendarEvent ev;
         if(!CalendarEventById(values[i].event_id, ev)) continue;
         if(ev.importance==CALENDAR_IMPORTANCE_HIGH || ev.importance==CALENDAR_IMPORTANCE_MODERATE)
           {
            FileWrite(fh,
                      TimeToString(values[i].time, TIME_DATE|TIME_MINUTES),
                      ccys[c],
                      (int)ev.importance,     // 2=orange, 3=red
                      ev.name);
            total++;
           }
        }
     }
   FileClose(fh);
   PrintFormat("CalDump: raw=%d  high+moderate=%d  err=%d", raw, total, GetLastError());
   return(INIT_SUCCEEDED);
  }

void OnTick() {}
double OnTester() { return(0.0); }
