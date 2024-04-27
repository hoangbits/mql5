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

input double   lotSize=1.5;
input double   riskPercentPerTrade=0.0;
input bool     useRiskPercentPerTrade=false;
input int      emaPeriod=8;
input int      checkEveryMinutes=15; 
input string   timeFrame="H1";
input string   tradingSymbol="GBPJPY+";
input string   symbolUJOnBroker="USDJPY+";
input bool     requiredClosedBothSideOfEMA=false;
//--- required pips from previous day to trade today some broker bullish/ some other bearish
input double   minPipsRequiredFromYesterday=0.3; 
input double   minPipsRequiredFromLastWeek=0.0; 
input double   addPipsToEMA=0.02; 



datetime previousRange = 0;
//--- related to EMA
int    emaHandle;
double MA_Buffer[];
ENUM_TIMEFRAMES htf_period = PERIOD_H4;
ENUM_TIMEFRAMES ltf_period = PERIOD_M15;


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
//--- todo copy it to ontick later
   Print("-------------------on init start-------------------"); 
   
   // TimeCurrent() (which returns the current time in seconds since 1970)
   previousRange = TimeCurrent() / (60 * checkEveryMinutes);
   emaHandle = iMA(tradingSymbol,ltf_period,emaPeriod,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(MA_Buffer,true);
   
   handle_new_tick();
 
  
  
   
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
   // get current range
   datetime currenTFtRange = TimeCurrent() / (60 * checkEveryMinutes);
    
   if(currenTFtRange != previousRange) {
      // when new hourly candle start to form      
      handle_new_tick();
      previousRange = currenTFtRange;
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

void handle_new_tick(){
   //string todayBias = get_htf_bias();
   string todayBias = get_ict_bias();
   //string todayBias = get_previous_week_bias();
   Print("main::todayBias: ", todayBias);      
   // can place max 2 trade per day
   if (!isAlreadyPlaceATradeToday() && todayBias != "NOBIAS") {
      //--- Get the current Bid price
      double currentBid = SymbolInfoDouble(tradingSymbol, SYMBOL_BID);   
      //--- Get the current Ask price
      double currentAsk = SymbolInfoDouble(tradingSymbol, SYMBOL_ASK);
      Print("handle_new_tick::Current Bid: ", currentBid);
      Print("handle_new_tick::Current Ask: ", currentAsk);          

      if(CopyBuffer(emaHandle,0,0,2,MA_Buffer)!=2) return;  
      //--- MA_Buffer[0] is current candle EMA      
      Print("handle_new_tick::MA_Buffer[0]: ", MA_Buffer[0]);              
      //Print("Media_Movil[0] = ", MA_Buffer[0] ,"\n","Media_Movil[1] = ",DoubleToString(MA_Buffer[1],6));
      
      //--- START handle povot point
      double xOpen = iOpen(tradingSymbol, htf_period, 1);
      double xHigh = iHigh(tradingSymbol, htf_period, 1);
      double xLow = iLow(tradingSymbol, htf_period, 1);
      double xClose = iClose(tradingSymbol, htf_period, 1);
      

      double vPP = (xHigh+xLow+xClose) / 3;
      double vR1 = vPP+(vPP-xLow);
      double vS1 = vPP-(xHigh - vPP);
      Print("handle_new_tick:: bias: ", todayBias);
      Print("handle_new_tick:: xOpen: ", xOpen);
      Print("handle_new_tick:: xHigh: ", xHigh);
      Print("handle_new_tick::xLow: ", xLow);
      Print("handle_new_tick::xClose: ", xClose);
      Print("vhandle_new_tick:: R1: ", vR1);
      Print("handle_new_tick:: vS1: ", vS1);
      //--- END handle povot point
      
      if(todayBias == "BUY") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed below EMA9
           
            if (currentAsk < (MA_Buffer[0] - addPipsToEMA)){
               //Print("handle_new_tick::START LONG as currentAsk < ema9_hourly: ", currentAsk < MA_Buffer[0]);
               double sl = vS1;
               double potential_profit = vR1 - currentAsk;
               double potential_loss = currentAsk - vS1;
               if(potential_loss > potential_profit) {
                 sl = currentAsk - potential_profit;
               }
               place_trade(ORDER_TYPE_BUY, sl , vR1);                
            }
            else {
               Print("handle_new_tick:: looking for BUY but currentASL is not < EMA9 hourly ");
            }
            
         }else{
           // TODO: might not need handle this 
           Print("not handle buy both side yet");          
         }
      }else if(todayBias == "SELL") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed above EMA9
            if (currentBid > (MA_Buffer[0] + addPipsToEMA)){
               Print("handle_new_tick::START SELL as currentBid > ema9_hourly: ", currentAsk > MA_Buffer[0]);
               double sl = vR1;
               double potential_profit = currentBid - vS1;
               double potential_loss = vR1 - currentBid;
               if(potential_loss > potential_profit) {
                 sl = currentBid + potential_profit;
               }   
               place_trade(ORDER_TYPE_SELL, sl, vS1);                                
            } else {
              Print("handle_new_tick:: looking for sell but currentbid is not > EMA9 hourly ");
            }
         }else{
            Print("not handle SELL both side yet");        
           // TODO:
         }
   
      }
      
   }else {
      Print("Done for the day, Trade already placed!");
   }
}


string get_htf_bias() {
   double previous_day_close_price, previous_day_open_price;          
   // Get previous trading day
   datetime prev_day = iTime(tradingSymbol, PERIOD_H4, 1);
   
   // Get shift for previous trading day's close price
   int shift = iBarShift(tradingSymbol, PERIOD_H4, prev_day);
   
   // Get previous trading day's close price
   previous_day_open_price = iOpen(tradingSymbol, PERIOD_H4, shift);
   previous_day_close_price = iClose(tradingSymbol, PERIOD_H4, shift);
   
   
   // Print previous trading day's close price
   //Print("Previous trading day's " , prev_day, " with open price: ", previous_day_open_price);   
   //Print("Previous trading day's " , prev_day, " with close price: ", previous_day_close_price);
   string bias = "NOBIAS";
   if(previous_day_open_price > previous_day_close_price )  {
      bias = "SELL";
   }
   
   if(previous_day_open_price < previous_day_close_price)  {
      bias = "BUY";
   }
   double previous_day_range_pips = previous_day_close_price - previous_day_open_price;
   if(MathAbs(previous_day_range_pips) < minPipsRequiredFromYesterday)  {
      bias = "NOBIAS";
   }
   //Print("get_htf_bias::previous_day_range_pips: ", previous_day_range_pips);
   //Print("get_htf_bias::minPipsRequiredFromYesterday: ", minPipsRequiredFromYesterday);
   
   Print("get_htf_bias:: prev_day ", prev_day, " bias value: " , bias);
   return bias;
}


string get_previous_week_bias() {
   double previous_week_close_price, previous_week_open_price;          
   // Get previous trading week
   datetime prev_week = iTime(tradingSymbol, PERIOD_W1, 1);
   
   // Get shift for previous trading week's close price
   int shift = iBarShift(tradingSymbol, PERIOD_W1, prev_week);
   
   // Get previous trading week's close price
   previous_week_open_price= iOpen(tradingSymbol, PERIOD_W1, shift);
   previous_week_close_price = iClose(tradingSymbol, PERIOD_W1, shift);
   
   
   // Print previous trading week's close price
   //Print("Previous trading week's " , prev_week, " with open price: ", previous_week_open_price);   
   //Print("Previous trading week's " , prev_week, " with close price: ", previous_week_close_price);
   string bias = "NOBIAS";
   if(previous_week_open_price > previous_week_close_price)  {
      bias = "SELL";
   }
   
   if(previous_week_open_price < previous_week_close_price)  {
      bias = "BUY";
   }
   double previous_week_range_pips = previous_week_close_price - previous_week_open_price;
   if(MathAbs(previous_week_range_pips) < minPipsRequiredFromLastWeek)  {
      bias = "NOBIAS";
   }
   //Print("get_previous_week_bias::previous_week_range_pips: ", previous_week_range_pips);
   //Print("get_previous_week_bias::minPipsRequiredFromLastWeek: ", minPipsRequiredFromLastWeek);
   
   Print("get_previous_week_bias:: prev_week ", prev_week, " bias value: " , bias);
   return bias;
}

int total_trade_placed_today(){
    datetime today_start_time = iTime(tradingSymbol, PERIOD_H4, 0);    
    int total_trade_placed_today = 0;    
    HistorySelect(today_start_time, TimeCurrent());
    for(int i = HistoryOrdersTotal() - 1; i >= 0; i--)
    {
        ulong ticket=HistoryOrderGetTicket(i);             
        if (ticket > 0)
        {
            datetime time_setup = (datetime)HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP);
            if(time_setup >= today_start_time && HistoryOrderGetString(ticket,ORDER_SYMBOL) == tradingSymbol)
            {                
                total_trade_placed_today = total_trade_placed_today + 1;                                               
            }
        }
    }            
    Print("total_trade_placed_today:: today_start_time:", today_start_time ," total_trade_placed_today: ", total_trade_placed_today);
    return total_trade_placed_today;    
}

bool isAlreadyPlaceATradeToday(){
    datetime today_start_time = iTime(tradingSymbol, htf_period, 0);
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


//+------------------------------------------------------------------+
//| Calculates the lot size based on symbol, entry price, SL, and TP |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double entryPrice, double stopLoss, double riskPerTrade)
{
    double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE); // 0.001
    double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE); // 100.0        
    double pointValue = tickSize * tick_value; // 0.1
      
    double stopLossPips = MathAbs(entryPrice - stopLoss) / pointValue; // 40 or 50 or 60... pips
    
    double riskAmount = AccountInfoDouble(ACCOUNT_EQUITY) * riskPerTrade; // e.g 150 usd over 50pip
    double expect_usd_per_1_lot = riskAmount / stopLossPips; // e.g 3 usd per pip
        
    // 1 lot(1pip) cost 7 usd
    //-> find lot to cost 3 usd 
    // lot_value = (1 * 3 as riskamopunt) / 7 asonepipvalue
    
    
    Print("CalculateLotSize::tickSize ", tickSize);
    Print("CalculateLotSize::tickValue ", tick_value);
    Print("CalculateLotSize::pointValue ", pointValue);
    Print("CalculateLotSize::riskPerTrade: ", riskPerTrade, " ACCOUNT_EQUITY ", AccountInfoDouble(ACCOUNT_EQUITY));
    
    
    
    MqlTick latest_price_uj;   // To get the latest price USDJPY
    SymbolInfoTick(symbolUJOnBroker, latest_price_uj);
    double one_lot_value_usd = (0.01 / latest_price_uj.ask) * 100000;
    
    Print("CalculateLotSize::latest_price_uj.ask", latest_price_uj.ask);
    Print("CalculateLotSize::riskAmount ", riskAmount);
    Print("CalculateLotSize::stopLossPips ", stopLossPips);
    Print("CalculateLotSize::expect_usd_per_1_lot ", expect_usd_per_1_lot); //  e.g depends on Risk amount and pip SL
    Print("CalculateLotSize::one_lot_value_usd", one_lot_value_usd); //  e.g: 7 usd
    
    double trade_lot_size = NormalizeDouble(expect_usd_per_1_lot / one_lot_value_usd, 2);
    Print("CalculateLotSize::trade_lot_size ", trade_lot_size);
    return trade_lot_size;
}




void place_trade(ENUM_ORDER_TYPE orderType,double stopLossPrice,double takeProfitPrice) {
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   ZeroMemory(request);  // Initialize memory to zero
   ZeroMemory(result);
   MqlTick latest_price;   // To get the latest price
   SymbolInfoTick(tradingSymbol, latest_price);
   double entry_price;
   if(orderType == ORDER_TYPE_BUY) {
     entry_price = latest_price.ask;      
   }else if (orderType == ORDER_TYPE_SELL) {
     entry_price = latest_price.bid;            
   }
   
   double trade_lot_size = lotSize;
   if(riskPercentPerTrade > 0.0) {      
      //--- Calculate lot size for riskPercentPerTrade% risk
      trade_lot_size = CalculateLotSize(tradingSymbol, entry_price, stopLossPrice, riskPercentPerTrade/100);
      Print("Lot size for riskPercentPerTrade:", riskPercentPerTrade ,"% risk: ", trade_lot_size );
   } 
   Print("lotSize Placing: ", trade_lot_size );

   
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = tradingSymbol;
   request.volume = trade_lot_size;
   request.type = orderType;
   request.type_filling = ORDER_FILLING_IOC;   
   request.price = entry_price;
   
   Print("place_trade::", orderType ,"  at price:", request.price);
   Print("place_trade::Stop Loss set at:", stopLossPrice);
   Print("place_trade::Take Profit set at:", takeProfitPrice);
   request.deviation = 10;
   request.magic = 123456;

   request.sl = stopLossPrice;
   request.tp = takeProfitPrice;

  
   Print(SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE));

   //--- send the request
   if(!OrderSend(request,result)){
     PrintFormat("OrderSend error %d",GetLastError());     // if unable to send the request, output the error code
   }
   
   //--- information about the operation
   //--- when DEBUG also check Journal tab(beside of expert tab.)
   PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
   Print("place_trade::result.comment: ",result.comment);
   Print("place_trade::result.request_id: ",result.request_id);
   Print("place_trade11::result.retcode_external", result.retcode_external);
   
}



// true if high1-previous day's high igher than two prevous day's hight.
bool is_wick_higher(double high1, double high2) {
   return high1 > high2;
}

// true if low1-previous day's low lower than two prevous day's low.
bool is_wick_lower(double low1, double low2) {
   return low1 < low2;
}


// is body higher than wick_high2
bool is_body_higher(double body_closed1, double high2 ) {
   return body_closed1 > high2;
}

// is body lower than wick_low1
bool is_body_lower(double body_closed1, double low2) {
   return body_closed1 < low2;
}

bool is_ict_bullish(double low1, double close1, double low2, double high2) {
   // wick lower then closed higher
   if(is_wick_lower(low1,low2) && close1 > low2 && is_body_higher(close1,high2)) {
      return true;
   }
   //if(is_body_higher(close1,high2)) {
     // return true;
   //}   
   return false;
}

bool is_ict_bearish(double high1, double close1, double low2, double high2) {
   // wick higher then closed lower
   if(is_wick_higher(high1, high2) && close1 < high2 && is_body_lower(close1,low2)) {
      return true;
   }
   //if(is_body_lower(close1,low2)) {
     // return true;
   //}   
   return false;
}



// green or red
string get_candle_color(datetime day) {
   // datetime prev_day = iTime(tradingSymbol, htf_period, 1);
   
   // Get shift to trading day
   int shift = iBarShift(tradingSymbol, htf_period, day);
   
   double day_open_price = iOpen(tradingSymbol, htf_period, shift);
   double day_close_price = iClose(tradingSymbol, htf_period, shift);
   
   
   if(day_open_price > day_close_price)  {
      return "RED";
   }else if(day_open_price < day_close_price)  {
      return "GREEN";
   }   
   return "NO_COLOR";
}

// previous day 1 is bullish bigger and close above previous day 2
//bool closed_above_from_previous_wick(double high1,double body_close2) {
  // return body_close2 > high1; // is body lower
//}

//bool closed_below_from_previous_wick(double low1,double body_close2) {
  // return body_close2 < low1; // is body lower
//}

// low1 is low of yerterday. 1 is every thing on yesterday
// 2 is everything on 2 previous day
bool is_bias_neutral(string one_preday_candle_color, double low1, double high1, double body_close1, double low2, double high2, double body_close2) {
   
   // previous day candle color
   
   
   
   // candle 2 bigger than candle1  :if both is_wick_higher and is_wick_higher true   
   if(is_wick_higher(high1, high2) && is_wick_lower(low1, low2)){
      
      // START Can comment out to test     
      
      if(one_preday_candle_color == "NO_COLOR") {
         return true; // neutral
      } else if(one_preday_candle_color == "GREEN" && is_body_higher(body_close1, high2)){
         return false; // bias are BULLISH. but accept that duplicated code
      } else if(one_preday_candle_color == "RED" && is_body_lower(body_close1, low2)){
         return false;  // bias are bearish but accept duplicated code
      }
      
      // END Can comment out to test
      return true;
   } 
   // candle 2 smallerthan candle1  :if both is_wick_higher and is_wick_higher false   
   if(is_wick_higher(high1, high2) == false && is_wick_lower(low1, low2) == false ){
      return true;
   } 
   
   return false;

}

string get_ict_bias() {
   double previous_day_close_price, previous_day_open_price;          
   // Get previous trading day
   datetime prev_day = iTime(tradingSymbol, htf_period, 1);
   datetime two_prev_day = iTime(tradingSymbol, htf_period, 2);
   
   // Get shift for previous trading day's close price
   int shift = iBarShift(tradingSymbol, htf_period, prev_day);
   int shift_two_day = iBarShift(tradingSymbol, htf_period, two_prev_day);
   
   // Get previous trading day's close price
   double prev_day_open_price = iOpen(tradingSymbol, htf_period, shift);
   double prev_day_close_price = iClose(tradingSymbol, htf_period, shift);
   double prev_day_high_price = iHigh(tradingSymbol, htf_period, shift);
   double prev_day_low_price = iLow(tradingSymbol, htf_period, shift);
   
   //two_previous_day_open_price = iOpen(tradingSymbol, htf_period, shift_two_day);
   double two_prev_day_close_price = iClose(tradingSymbol, htf_period, shift_two_day);
   double two_prev_day_high_price = iHigh(tradingSymbol, htf_period, shift_two_day);
   double two_prev_day_low_price = iLow(tradingSymbol, htf_period, shift_two_day);
   
   string one_preday_candle_color = get_candle_color(prev_day);
   //bool is_bias_neutral = is_bias_neutral(one_preday_candle_color, prev_day_low_price,prev_day_high_price, prev_day_close_price, two_prev_day_low_price, two_prev_day_high_price, two_prev_day_close_price);
   //Print("is_bias_neutral: ", is_bias_neutral);
   bool is_bias_neutral = false;
   double previous_day_range_pips = previous_day_close_price - prev_day_open_price;
   if(MathAbs(previous_day_range_pips) < minPipsRequiredFromYesterday)  {
      return  "NOBIAS";
   }
   if (!is_bias_neutral) {
      
      if(one_preday_candle_color == "GREEN" && is_ict_bullish(prev_day_low_price, prev_day_close_price, two_prev_day_low_price, two_prev_day_high_price)){
         return "BUY";
      }
      
      if(one_preday_candle_color == "RED" && is_ict_bearish(prev_day_high_price, prev_day_close_price, two_prev_day_low_price, two_prev_day_high_price)){
         return "SELL";
      }
   } else 
   {
      return "NOBIAS";     
   }
   return "NOBIAS";     
}
