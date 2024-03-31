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
input int      emaPeriod=9;
input string   timeFrame="H1";
input string   tradingSymbol="GBPJPY";
input bool     requiredClosedBothSideOfEMA=false;
//--- required pips from previous day to trade today some broker bullish/ some other bearish
input int      minPipsRequiredFromYesterday=0; 


datetime previousHour = 0;
//--- related to EMA
int    emaHandle;
double MA_Buffer[];


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
//--- todo copy it to ontick later
   Print("-------------------on init start-------------------"); 
   // TimeCurrent() (which returns the current time in seconds since 1970)
   previousHour = TimeCurrent() / (60 * 60);
   emaHandle = iMA(tradingSymbol,PERIOD_H1,9,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(MA_Buffer,true);
   
   handle_new_hourly();
 
  
  
   
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
   // get current hour
   datetime currentHour = TimeCurrent() / (60 * 60);
   if(currentHour != previousHour) {
      // when new hourly candle start to form
      handle_new_hourly();
      previousHour = currentHour;
   }
      
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

void handle_new_hourly(){
   string todayBias = get_daily_bias();
   Print("main::todayBias: ", todayBias);
   
    if (!isAlreadyPlaceATradeToday() && todayBias != "NOBIAS") {
      //--- Get the current Bid price
      double currentBid = SymbolInfoDouble(tradingSymbol, SYMBOL_BID);   
      //--- Get the current Ask price
      double currentAsk = SymbolInfoDouble(tradingSymbol, SYMBOL_ASK);
      Print("handle_new_hourly::Current Bid: ", currentBid);
      Print("handle_new_hourly::Current Ask: ", currentAsk);              
      
      if(CopyBuffer(emaHandle,0,0,2,MA_Buffer)!=2) return;  
      //--- MA_Buffer[0] is current candle EMA      
      Print("handle_new_hourly::MA_Buffer[0]: ", MA_Buffer[0]);              
      //Print("Media_Movil[0] = ", MA_Buffer[0] ,"\n","Media_Movil[1] = ",DoubleToString(MA_Buffer[1],6));
      if(todayBias == "BUY") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed below EMA9
           
            if (currentAsk < MA_Buffer[0]){
               Print("handle_new_hourly::START LONG as currentAsk < ema9_hourly: ", currentAsk < MA_Buffer[0]);
            }
            
         }else{
           // TODO: might not need handle this           
         }
      }else if(todayBias == "SELL") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed above EMA9
             if (currentAsk > MA_Buffer[0]){
               Print("handle_new_hourly::START SELL as currentBid > ema9_hourly: ", currentAsk > MA_Buffer[0]);
            }
         }else{
           // TODO:
         }
   
      }
      
   }else {
      Print("Done for the day, Trade already placed!");
   }
}


string get_daily_bias() {
   double previous_day_close_price, previous_day_open_price;          
   // Get previous trading day
   datetime prev_day = iTime(tradingSymbol, PERIOD_D1, 1);
   
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
   Print("get_daily_bias::previous_day_range_pips: ", previous_day_range_pips);
   Print("get_daily_bias::minPipsRequiredFromYesterday: ", minPipsRequiredFromYesterday);
   
   Print("get_daily_bias:: prev_day ", prev_day, " bias value: " , bias);
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

    Print("isAlreadyPlaceATradeToday::today_start_time value:", today_start_time);
    Print("isAlreadyPlaceATradeToday::is placed trade Today: ", tradePlacedToday);
    return tradePlacedToday;
}