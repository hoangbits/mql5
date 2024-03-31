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
//--- required pips from previous day to trade today some broker bullish/ some other bearish
input int      minPipsRequiredFromYesterday=0; 

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
//--- todo copy it to ontick later

   string todayBias = get_daily_bias();
   Print("main::todayBias: ", todayBias);
   double pp_up, pp_down;
   
 
   if (!isAlreadyPlaceATradeToday()) {
      if(todayBias == "BUY") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed below EMA9
            
            
         }else{
           // TODO: might not need handle this           
         }
   
      }else if(todayBias == "SELL") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed above EMA9
         }else{
           // TODO:
         }
   
      }else if(todayBias == "NOBIAS"){
         Print("No bias, no trade!");
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
   Print("Previous trading day's " , prev_day, " with open price: ", previous_day_open_price);   
   Print("Previous trading day's " , prev_day, " with close price: ", previous_day_close_price);
   string bias = "NOBIAS";
   if(previous_day_open_price > previous_day_close_price)  {
      bias = "SELL";
   }
   
   if(previous_day_open_price < previous_day_close_price)  {
      bias = "SELL";
   }
   double previous_day_range_pips = previous_day_close_price - previous_day_open_price;
   if(MathAbs(previous_day_range_pips) < minPipsRequiredFromYesterday)  {
      bias = "NOBIAS";
   }
   Print("previous_day_range_pips: ", previous_day_range_pips);
   Print("minPipsRequiredFromYesterday: ", minPipsRequiredFromYesterday);
   
   Print("day ", prev_day, " bias value: " , bias);
   return bias;
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

    Print("isAlreadyPlaceATradeToday today_start_time value:", today_start_time);
    Print("isAlreadyPlaceATradeToday is placed trade Today: ", tradePlacedToday);
    return tradePlacedToday;
}