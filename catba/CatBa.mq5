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

input double    lotSize=0.05;
input double    riskPercentPerTrade=1.0;
input bool     useRiskPercentPerTrade=false;
input int      emaPeriod=7;
input string   timeFrame="H1";
input string   tradingSymbol="GBPJPY+";
input bool     requiredClosedBothSideOfEMA=false;
//--- required pips from previous day to trade today some broker bullish/ some other bearish
input double   minPipsRequiredFromYesterday=0.3; 
input double   minPipsRequiredFromLastWeek=0.6; 

input double   secondEntryProtractionPips=0.09; 
input double   addPipsToEMA=0.05; 


datetime previousHour = 0;
//--- related to EMA
int    emaHandle;
double MA_Buffer[];
double last_trade_open_price = 0.0;

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
   emaHandle = iMA(tradingSymbol,PERIOD_H1,emaPeriod,0,MODE_EMA,PRICE_CLOSE);
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
   //string todayBias = get_daily_bias();
   string todayBias = get_previous_week_bias();
   Print("main::todayBias: ", todayBias);
   double first_trade_open_price;
   int total_trades = total_trade_placed_today(first_trade_open_price);
   // can place max 2 trade per day
    if (total_trades < 2 && todayBias != "NOBIAS") {
      //--- Get the current Bid price
      double currentBid = SymbolInfoDouble(tradingSymbol, SYMBOL_BID);   
      //--- Get the current Ask price
      double currentAsk = SymbolInfoDouble(tradingSymbol, SYMBOL_ASK);
      Print("handle_new_hourly::Current Bid: ", currentBid);
      Print("handle_new_hourly::Current Ask: ", currentAsk);              
      Print("handle_new_hourly::first_trade_open_price: ", first_trade_open_price);              
      if(CopyBuffer(emaHandle,0,0,2,MA_Buffer)!=2) return;  
      //--- MA_Buffer[0] is current candle EMA      
      Print("handle_new_hourly::MA_Buffer[0]: ", MA_Buffer[0]);              
      //Print("Media_Movil[0] = ", MA_Buffer[0] ,"\n","Media_Movil[1] = ",DoubleToString(MA_Buffer[1],6));
      
      //--- START handle povot point
      double xHigh = iHigh(tradingSymbol, PERIOD_D1, 1);
      double xLow = iLow(tradingSymbol, PERIOD_D1, 1);
      double xClose = iClose(tradingSymbol, PERIOD_D1, 1);

      double vPP = (xHigh+xLow+xClose) / 3;
      double vR1 = vPP+(vPP-xLow);
      double vS1 = vPP-(xHigh - vPP);
      //Print("handle_new_hourly:: xHigh: ", xHigh);
      //Print("handle_new_hourly::xLow: ", xLow);
      //Print("handle_new_hourly::xClose: ", xClose);
      Print("vhandle_new_hourly:: R1: ", vR1);
      Print("handle_new_hourly:: vS1: ", vS1);
      //--- END handle povot point
      
      if(todayBias == "BUY") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed below EMA9
           
            if (currentAsk < (MA_Buffer[0] - addPipsToEMA)){
               //Print("handle_new_hourly::START LONG as currentAsk < ema9_hourly: ", currentAsk < MA_Buffer[0]);
               double sl = vS1;
               double potential_profit = vR1 - currentAsk;
               double potential_loss = currentAsk - vS1;
               if(potential_loss > potential_profit) {
                 sl = currentAsk - potential_profit;
               } else {
                  Print("last_trade_open_price000000000000", last_trade_open_price);
                  if (total_trades == 0) {
                    place_trade(ORDER_TYPE_BUY, sl, vR1, last_trade_open_price, true);
                  } else if(total_trades == 1 && currentAsk < last_trade_open_price - secondEntryProtractionPips) {                 
                    Print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&");
                    //sl = vS1;
                    //place_trade(ORDER_TYPE_BUY, sl, vR1, last_trade_open_price, false);
                  }
                  
               }
               
            }
            else {
            Print("handle_new_hourly:: looking for BUY but currentASL is not < EMA9 hourly ");
            }
            
         }else{
           // TODO: might not need handle this 
           Print("not handle buy both side yet");          
         }
      }else if(todayBias == "SELL") {
         if(!requiredClosedBothSideOfEMA) {
            //--- check if H1 candle closed above EMA9
            if (currentBid > (MA_Buffer[0] + addPipsToEMA)){
               Print("handle_new_hourly::START SELL as currentBid > ema9_hourly: ", currentAsk > MA_Buffer[0]);
               double sl = vR1;
               double potential_profit = currentBid - vS1;
               double potential_loss = vR1 - currentBid;
               if(potential_loss > potential_profit) {
                 sl = currentBid + potential_profit;
               }   else {                            
                  Print("last_trade_open_price111111111111111111", last_trade_open_price);
                  if (total_trades == 0) {
                    place_trade(ORDER_TYPE_SELL, sl, vS1, last_trade_open_price, true);    
                  } else if(total_trades == 1 && currentBid > last_trade_open_price + secondEntryProtractionPips) {                 
                    Print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%");
               //      sl = vR1;
                    //place_trade(ORDER_TYPE_SELL, sl, vS1, last_trade_open_price, false);    
                  }         
               }                 
            } else {
              Print("handle_new_hourly:: looking for sell but currentbid is not > EMA9 hourly ");
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
   //Print("Previous trading day's " , prev_day, " with open price: ", previous_day_open_price);   
   //Print("Previous trading day's " , prev_day, " with close price: ", previous_day_close_price);
   string bias = "NOBIAS";
   if(previous_day_open_price > previous_day_close_price)  {
      bias = "SELL";
   }
   
   if(previous_day_open_price < previous_day_close_price)  {
      bias = "BUY";
   }
   double previous_day_range_pips = previous_day_close_price - previous_day_open_price;
   if(MathAbs(previous_day_range_pips) < minPipsRequiredFromYesterday)  {
      bias = "NOBIAS";
   }
   //Print("get_daily_bias::previous_day_range_pips: ", previous_day_range_pips);
   //Print("get_daily_bias::minPipsRequiredFromYesterday: ", minPipsRequiredFromYesterday);
   
   Print("get_daily_bias:: prev_day ", prev_day, " bias value: " , bias);
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

int total_trade_placed_today(double &first_trade_price){
    datetime today_start_time = iTime(tradingSymbol, PERIOD_D1, 0);
    //int totalOrders = HistoryOrdersTotal()();
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
                //double open_price = HistoryOrderGetDouble(ticket,ORDER_PRICE_OPEN);
                //double trade_tp = HistoryOrderGetDouble(ticket, ORDER_TP);                                                 
                  //Print("AAAAAAAAAAAAAAAAAAAA open_price", open_price);
                  //Print("BBBBBBBBBBBBB trade_tp", trade_tp);
                if(total_trade_placed_today == 0 ) {
                  //first_trade_price = HistoryOrderGetDouble(ticket, ORDER_PRICE_OPEN);                                                 
                  //double first_trade_tp = HistoryOrderGetDouble(ticket, ORDER_TP);                                                 
                  //double first_trade_price = open_price;
                  //Print("found first_trade_price", first_trade_price);
                  //Print("found first_trade_tp", first_trade_tp);
                  
                }
                total_trade_placed_today = total_trade_placed_today + 1;                               
                
            }
        }
    }            
    Print("total_trade_placed_today:: today_start_time:", today_start_time ," total_trade_placed_today: ", total_trade_placed_today);
    return total_trade_placed_today;
    
    
}




void place_trade(ENUM_ORDER_TYPE orderType,double stopLossPrice,double takeProfitPrice, double &last_trade_open_price, bool is_first_trade) {

    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    ZeroMemory(request);  // Initialize memory to zero
    ZeroMemory(result);
    MqlTick latest_price;   // To get the latest price
    SymbolInfoTick(tradingSymbol, latest_price);
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = tradingSymbol;
    request.volume = lotSize;
    request.type = orderType;
    request.type_filling = ORDER_FILLING_IOC;
    if(orderType == ORDER_TYPE_BUY) {
      request.price = latest_price.ask;
      if (is_first_trade == true) {
         last_trade_open_price = latest_price.ask;
      }
      
    }else if (orderType == ORDER_TYPE_SELL) {
      request.price = latest_price.bid;
      if (is_first_trade == true) {
        last_trade_open_price = latest_price.bid;
      }
      
    }
    
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
