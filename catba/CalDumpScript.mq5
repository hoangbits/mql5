//+------------------------------------------------------------------+
//| CalDumpScript.mq5 — run on a LIVE chart (drag onto any chart).    |
//| Dumps ALL high(red)+moderate(orange) impact GBP/JPY/USD economic  |
//| events from 2016 to now into Common\Files\calendar_dump.csv.      |
//| The calendar API works on a live chart (it is blocked in tester). |
//+------------------------------------------------------------------+
#property copyright "Hoang Le"
#property version   "1.00"
#property script_show_inputs

input datetime FromDate = D'2016.01.01 00:00';
input datetime ToDate   = D'2026.07.03 00:00';

void OnStart()
  {
   int fh = FileOpen("calendar_dump.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh==INVALID_HANDLE) { Print("CalDump: cannot open file, err=",GetLastError()); return; }
   FileWrite(fh, "time","currency","importance","event");

   string ccys[] = {"GBP","JPY","USD"};
   int total=0, raw=0;

   for(int c=0; c<ArraySize(ccys); c++)
     {
      MqlCalendarValue values[];
      int n = CalendarValueHistory(values, FromDate, ToDate, NULL, ccys[c]);
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
                      (int)ev.importance,     // 2=orange/moderate, 3=red/high
                      ev.name);
            total++;
           }
        }
     }
   FileClose(fh);
   PrintFormat("CalDump DONE: raw=%d events, high+moderate=%d written, err=%d", raw, total, GetLastError());
   Comment(StringFormat("CalDump done: %d high/moderate events written to Common\\Files\\calendar_dump.csv", total));
  }
