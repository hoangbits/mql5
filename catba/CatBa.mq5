//+------------------------------------------------------------------+
//|                                                   CatBa.mq5 |
//|                                                         Hoang Le |
//|                             https://www.mql5.com/en/users/ghoang |
//+------------------------------------------------------------------+
#property copyright "Hoang Le"
#property link      "https://www.mql5.com/en/users/ghoang"
#property version   "1.00"

//---import 
#include <Trade\SymbolInfo.mqh>


//--- input parameters
input float    fixedLotSize=1.0;
input float    riskPercentPerTrade=1.0;
input bool     useRiskPercentPerTrade=false;
input int      emaLength=9;
input string   timeFrame="H1";
input string   tradingSymbol="GBPJPY";
input bool     requiredClosedBothSideOfEMA=false;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
   string todayBias = get_daily_bias();
   double pp_up, pp_down;
   
   Print("today bias:", todayBias);
   if (!isAlreadyPlaceATradeToday()) {
      if(todayBias == "BUY") {
         if(!requiredClosedBothSideOfEMA) {
            
         }else{
           // TODO:
         }
   
      }else
      {
      // bias sell
         if(!requiredClosedBothSideOfEMA) {
            
         }else{
           // TODO:
         }
      }
   }else {
      Print("Done for the day, Trade already placed!");
   }
   
  
   
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
   
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
   //
  }
//+------------------------------------------------------------------+
//| Trade function                                                   |
//+------------------------------------------------------------------+
void OnTrade()
  {
//---
   
  }
//+------------------------------------------------------------------+


string get_daily_bias() {
   double previous_day_close_price, previous_day_open_price;          
   // Get previous trading day
   datetime prev_day = iTime(tradingSymbol, PERIOD_D1, 0);
   
   // Get shift for previous trading day's close price
   int shift = iBarShift(tradingSymbol, PERIOD_D1, prev_day);
   
   // Get previous trading day's close price
   previous_day_open_price = iOpen(tradingSymbol, PERIOD_D1, shift);
   previous_day_close_price = iClose(tradingSymbol, PERIOD_D1, shift);
   
   
   // Print previous trading day's close price
   Print("Previous trading day's open price: ", previous_day_open_price);
   Print("Previous trading day's close price: ", previous_day_close_price);
   if(previous_day_open_price > previous_day_close_price)  {
      return "SELL";
   }else{
      return "BUY";
   }
}

bool isAlreadyPlaceATradeToday(){
    datetime today_start_time = iTime(tradingSymbol, PERIOD_D1, 0);
    //int totalOrders = HistoryOrdersTotal()();
    bool tradePlacedToday = false;
    HistorySelect(today_start_time, TimeCurrent());

    for(int i = HistoryOrdersTotal() - 1; i >= 0; i--)
    {
        ulong ticket=HistoryOrderGetTicket(i);
        if (ticket > 0)
        {
            datetime time_setup = (datetime)HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP);
            if(time_setup >= today_start_time && HistoryOrderGetString(ticket,ORDER_SYMBOL) == tradingSymbol)
            {
                tradePlacedToday = true;
                break;
            }
        }
    }            

    Print("today_start_time value:", today_start_time);
    Print("is placed trade Today: ", tradePlacedToday);
    return tradePlacedToday;
}