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

input double   lotSize=0.0;
input double   riskPercentPerTrade=0.2;
input bool     useRiskPercentPerTrade=true;
input int      emaPeriod=8;
input int      checkEveryMinutes=12;
input string   timeFrame="H1";
input string   tradingSymbol="GBPJPY";
input string   symbolUJOnBroker="USDJPY";
input bool     requiredClosedBothSideOfEMA=false;
//--- required pips from previous day to trade today some broker bullish/ some other bearish
input double   minPipsRequiredFromYesterday=0.28;
//--- upper cap for yesterday's body; big bodies mean-revert (research H1)
input double   maxPipsRequiredFromYesterday=999.0;
//--- size risk from initial deposit instead of compounding equity (research H12b)
input bool     riskOnInitialDeposit=false;
//--- cap SL so risk<=reward (legacy behavior); tight capped SLs are the
//--- toxic trades identified in research H12b (research H8a)
input bool     useRRCapOnSL=true;
//--- ATR(14,D1)-scaled exits instead of pivot R1/S1 targets (research H8b)
input bool     useAtrExits=false;
input double   atrSlMult=1.0;
input double   atrTpMult=1.5;
//--- entry-hour windows in SERVER time (= NY+7 on Darwinex); -1 = always
//--- (research H4: ICT killzones; London 9-12, NY 14-17 server)
input int      kz1StartHour=-1;
input int      kz1EndHour=-1;
input int      kz2StartHour=-1;
input int      kz2EndHour=-1;
input double   minPipsRequiredFromLastWeek=0.0;
input double   addPipsToEMA=0.11;
input double   DistanceToTriggerBE=0.72;
input double   add_pip_to_sl=0.2;

double distance_to_trigger_be = DistanceToTriggerBE;
int EXPERT_MAGIC = 042024;
double g_initial_equity = 0.0;   // captured in OnInit; base for riskOnInitialDeposit

datetime previousRange = 0;
datetime previous_check_sl_range = 0;
int      check_sl_every_minutes = 1;
//--- related to EMA
int    emaHandle;
double MA_Buffer[];
//--- daily ATR for H8b exits
int    atrHandle;
double ATR_Buffer[];




//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
//--- todo copy it to ontick later
   Print("-------------------on init start-------------------");
   g_initial_equity = AccountInfoDouble(ACCOUNT_EQUITY);
// TimeCurrent() (which returns the current time in seconds since 1970)
   previousRange = TimeCurrent() / (60 * checkEveryMinutes);
   previous_check_sl_range = TimeCurrent() / (60 * check_sl_every_minutes);

   emaHandle = iMA(tradingSymbol,PERIOD_H1,emaPeriod,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(MA_Buffer,true);
   atrHandle = iATR(tradingSymbol,PERIOD_D1,14);
   ArraySetAsSeries(ATR_Buffer,true);

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

   if(currenTFtRange != previousRange)
     {
      // when new hourly candle start to form
      handle_new_tick();
      previousRange = currenTFtRange;
     }

   datetime current_check_sl_range = TimeCurrent() / (60 * checkEveryMinutes);

   if(current_check_sl_range != previous_check_sl_range)
     {
      update_sl_to_be();;
      previous_check_sl_range = current_check_sl_range;
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

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void handle_new_tick()
  {
//--- H4: restrict new entries to configured killzone hours (server time)
   if(kz1StartHour >= 0)
     {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      bool inKz1 = (now.hour >= kz1StartHour && now.hour < kz1EndHour);
      bool inKz2 = (kz2StartHour >= 0 && now.hour >= kz2StartHour && now.hour < kz2EndHour);
      if(!inKz1 && !inKz2)
         return;
     }
   string todayBias = get_daily_bias();
//string todayBias = get_previous_week_bias();
   Print("main::todayBias: ", todayBias);
// can place max 2 trade per day
   if(!isAlreadyPlaceATradeToday() && todayBias != "NOBIAS")
     {
      //--- Get the current Bid price
      double currentBid = SymbolInfoDouble(tradingSymbol, SYMBOL_BID);
      //--- Get the current Ask price
      double currentAsk = SymbolInfoDouble(tradingSymbol, SYMBOL_ASK);
      Print("handle_new_tick::Current Bid: ", currentBid);
      Print("handle_new_tick::Current Ask: ", currentAsk);

      if(CopyBuffer(emaHandle,0,0,2,MA_Buffer)!=2)
         return;
      //--- MA_Buffer[0] is current candle EMA
      Print("handle_new_tick::MA_Buffer[0]: ", MA_Buffer[0]);
      //Print("Media_Movil[0] = ", MA_Buffer[0] ,"\n","Media_Movil[1] = ",DoubleToString(MA_Buffer[1],6));

      //--- START handle povot point
      double xHigh = iHigh(tradingSymbol, PERIOD_D1, 1);
      double xLow = iLow(tradingSymbol, PERIOD_D1, 1);
      double xClose = iClose(tradingSymbol, PERIOD_D1, 1);

      double vPP = (xHigh+xLow+xClose) / 3;
      double vR1 = vPP+(vPP-xLow);
      double vS1 = vPP-(xHigh - vPP);
      //Print("handle_new_tick:: xHigh: ", xHigh);
      //Print("handle_new_tick::xLow: ", xLow);
      //Print("handle_new_tick::xClose: ", xClose);
      Print("vhandle_new_tick:: R1: ", vR1);
      Print("handle_new_tick:: vS1: ", vS1);
      //--- END handle povot point

      //--- H8b: ATR(14,D1) of the last completed day for scaled exits
      double atrD1 = 0.0;
      if(useAtrExits)
        {
         if(CopyBuffer(atrHandle,0,1,1,ATR_Buffer)!=1)
            return;
         atrD1 = ATR_Buffer[0];
        }

      if(todayBias == "BUY")
        {
         if(!requiredClosedBothSideOfEMA)
           {
            //--- check if H1 candle closed below EMA9

            if(currentAsk < (MA_Buffer[0] - addPipsToEMA))
              {
               //Print("handle_new_tick::START LONG as currentAsk < ema9_hourly: ", currentAsk < MA_Buffer[0]);
               double sl = vS1;
               double tp = vR1;
               double potential_profit = vR1 - currentAsk;
               double potential_loss = currentAsk - vS1;
               if(useRRCapOnSL && potential_loss > potential_profit)
                 {
                  sl = currentAsk - (potential_profit);
                 }
               if(useAtrExits && atrD1 > 0.0)
                 {
                  sl = currentAsk - atrSlMult*atrD1;
                  tp = currentAsk + atrTpMult*atrD1;
                 }
               place_trade(ORDER_TYPE_BUY, sl, tp);
              }
            else
              {
               Print("handle_new_tick:: looking for BUY but currentASL is not < EMA9 hourly ");
              }

           }
         else
           {
            // TODO: might not need handle this
            Print("not handle buy both side yet");
           }
        }
      else
         if(todayBias == "SELL")
           {
            if(!requiredClosedBothSideOfEMA)
              {
               //--- check if H1 candle closed above EMA9
               if(currentBid > (MA_Buffer[0] + addPipsToEMA))
                 {
                  Print("handle_new_tick::START SELL as currentBid > ema9_hourly: ", currentAsk > MA_Buffer[0]);
                  double sl = vR1;
                  double tp = vS1;
                  double potential_profit = currentBid - vS1;
                  double potential_loss = vR1 - currentBid;
                  if(useRRCapOnSL && potential_loss > potential_profit)
                    {
                     sl = currentBid + (potential_profit );
                    }
                  if(useAtrExits && atrD1 > 0.0)
                    {
                     sl = currentBid + atrSlMult*atrD1;
                     tp = currentBid - atrTpMult*atrD1;
                    }
                  place_trade(ORDER_TYPE_SELL, sl, tp);
                 }
               else
                 {
                  Print("handle_new_tick:: looking for sell but currentbid is not > EMA9 hourly ");
                 }
              }
            else
              {
               Print("not handle SELL both side yet");
               // TODO:
              }

           }

     }
   else
     {
      Print("Done for the day, Trade already placed!");
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string get_daily_bias()
  {
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
   if(previous_day_open_price > previous_day_close_price)
     {
      bias = "SELL";
     }

   if(previous_day_open_price < previous_day_close_price)
     {
      bias = "BUY";
     }
   double previous_day_range_pips = previous_day_close_price - previous_day_open_price;
   if(MathAbs(previous_day_range_pips) < minPipsRequiredFromYesterday)
     {
      bias = "NOBIAS";
     }
   if(MathAbs(previous_day_range_pips) > maxPipsRequiredFromYesterday)
     {
      bias = "NOBIAS";   // oversized body: continuation edge measurably decays
     }
//Print("get_daily_bias::previous_day_range_pips: ", previous_day_range_pips);
//Print("get_daily_bias::minPipsRequiredFromYesterday: ", minPipsRequiredFromYesterday);

   Print("get_daily_bias:: prev_day ", prev_day, " bias value: ", bias);
   return bias;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string get_previous_week_bias()
  {
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
   if(previous_week_open_price > previous_week_close_price)
     {
      bias = "SELL";
     }

   if(previous_week_open_price < previous_week_close_price)
     {
      bias = "BUY";
     }
   double previous_week_range_pips = previous_week_close_price - previous_week_open_price;
   if(MathAbs(previous_week_range_pips) < minPipsRequiredFromLastWeek)
     {
      bias = "NOBIAS";
     }
//Print("get_previous_week_bias::previous_week_range_pips: ", previous_week_range_pips);
//Print("get_previous_week_bias::minPipsRequiredFromLastWeek: ", minPipsRequiredFromLastWeek);

   Print("get_previous_week_bias:: prev_week ", prev_week, " bias value: ", bias);
   return bias;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int total_trade_placed_today()
  {
   datetime today_start_time = iTime(tradingSymbol, PERIOD_D1, 0);
   int total_trade_placed_today = 0;
   HistorySelect(today_start_time, TimeCurrent());
   for(int i = HistoryOrdersTotal() - 1; i >= 0; i--)
     {
      ulong ticket=HistoryOrderGetTicket(i);
      if(ticket > 0)
        {
         datetime time_setup = (datetime)HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP);
         if(time_setup >= today_start_time && HistoryOrderGetString(ticket,ORDER_SYMBOL) == tradingSymbol)
           {
            total_trade_placed_today = total_trade_placed_today + 1;
           }
        }
     }
   Print("total_trade_placed_today:: today_start_time:", today_start_time," total_trade_placed_today: ", total_trade_placed_today);
   return total_trade_placed_today;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool isAlreadyPlaceATradeToday()
  {
   datetime today_start_time = iTime(tradingSymbol, PERIOD_D1, 0);
//int totalOrders = HistoryOrdersTotal()();
   bool tradePlacedToday = false;
   HistorySelect(today_start_time, TimeCurrent());

   for(int i = HistoryOrdersTotal() - 1; i >= 0; i--)
     {
      ulong ticket=HistoryOrderGetTicket(i);
      if(ticket > 0)
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
double CalculateLotSize(string symbol, double entry_price, double new_stop_loss, double riskPerTrade)
  {
   double tickSize  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);  // e.g 0.001 for GBPJPY
   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE); // value of 1 tick per 1.0 lot, in ACCOUNT currency
   double slDistance = MathAbs(entry_price - new_stop_loss);            // stop distance in price

   if(slDistance <= 0.0 || tickSize <= 0.0 || tickValue <= 0.0)
     {
      Print("CalculateLotSize:: invalid inputs slDistance=", slDistance,
            " tickSize=", tickSize, " tickValue=", tickValue);
      return 0.0;
     }

//--- money lost on 1.0 lot if price travels slDistance into the stop.
//--- tickValue is already in the deposit currency, so no manual FX conversion is needed.
   double lossPerLot = (slDistance / tickSize) * tickValue;
   double baseEquity = (riskOnInitialDeposit && g_initial_equity > 0.0)
                       ? g_initial_equity
                       : AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = baseEquity * riskPerTrade;
   double lots       = riskAmount / lossPerLot;

//--- snap to the broker's volume step and clamp to min/max
   double volMin  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double volMax  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double volStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   if(volStep > 0.0)
      lots = MathFloor(lots / volStep + 0.0000001) * volStep;
   if(lots < volMin)
     {
      Print("CalculateLotSize:: risk-based lot below min (", volMin,
            ") -> using min; actual risk will exceed the ", riskPerTrade*100, "% target");
      lots = volMin;
     }
   if(lots > volMax)
      lots = volMax;
   lots = NormalizeDouble(lots, 2);

   Print("CalculateLotSize:: equity=", AccountInfoDouble(ACCOUNT_EQUITY),
         " risk=", riskPerTrade, " riskAmount=", riskAmount,
         " slDistance=", slDistance, " lossPerLot=", lossPerLot, " lots=", lots);
   return lots;
  }




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void place_trade(ENUM_ORDER_TYPE orderType,double new_stop_lossPrice,double takeProfitPrice)
  {
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   ZeroMemory(request);  // Initialize memory to zero
   ZeroMemory(result);
   MqlTick latest_price;   // To get the latest price
   SymbolInfoTick(tradingSymbol, latest_price);
   double entry_price;
   if(orderType == ORDER_TYPE_BUY)
     {
      entry_price = latest_price.ask;
     }
   else
      if(orderType == ORDER_TYPE_SELL)
        {
         entry_price = latest_price.bid;
        }

   double trade_lot_size = lotSize;
   if(riskPercentPerTrade > 0.0)
     {
      //--- Calculate lot size for riskPercentPerTrade% risk
      trade_lot_size = CalculateLotSize(tradingSymbol, entry_price, new_stop_lossPrice, riskPercentPerTrade/100);
      Print("Lot size for riskPercentPerTrade:", riskPercentPerTrade,"% risk: ", trade_lot_size);
     }
   Print("lotSize Placing: ", trade_lot_size);



   request.action = TRADE_ACTION_DEAL;
   request.symbol = tradingSymbol;
   request.volume = trade_lot_size;
   request.type = orderType;
   request.type_filling = ORDER_FILLING_IOC;
   request.price = entry_price;

   Print("place_trade::", orderType,"  at price:", request.price);
   Print("place_trade::Stop Loss set at:", new_stop_lossPrice);
   Print("place_trade::Take Profit set at:", takeProfitPrice);
   request.deviation = 10;
   request.magic = EXPERT_MAGIC;

   request.sl = new_stop_lossPrice;
   request.tp = takeProfitPrice;


   Print(SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE));

//--- send the request
   if(!OrderSend(request,result))
     {
      PrintFormat("OrderSend error %d",GetLastError());     // if unable to send the request, output the error code
     }

//--- information about the operation
//--- when DEBUG also check Journal tab(beside of expert tab.)
   PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
   Print("place_trade::result.comment: ",result.comment);
   Print("place_trade::result.request_id: ",result.request_id);
   Print("place_trade11::result.retcode_external", result.retcode_external);

  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void update_sl_to_be()
  {
   MqlTradeRequest request;
   MqlTradeResult  result;
   double new_stop_loss,new_tp, sl, tp;
   int total=PositionsTotal(); // number of open positions
//--- iterate over all open positions
   for(int i=0; i<total; i++)
     {
      ZeroMemory(sl);
      ZeroMemory(tp);
      //--- parameters of the order
      ulong  position_ticket=PositionGetTicket(i);// ticket of the position
      string position_symbol=PositionGetString(POSITION_SYMBOL); // symbol
      int    digits=(int)SymbolInfoInteger(position_symbol,SYMBOL_DIGITS); // number of decimal places
      ulong  magic=PositionGetInteger(POSITION_MAGIC); // MagicNumber of the position
      double volume=PositionGetDouble(POSITION_VOLUME);    // volume of the position
      double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);  // open price of the position
      sl=PositionGetDouble(POSITION_SL);  // Stop Loss of the position
      tp=PositionGetDouble(POSITION_TP);  // Take Profit of the position
      Print("OILDDDDDDDDDDDD SL ", sl);
      double shouldRequestChange = false;

      ENUM_POSITION_TYPE type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);  // type of the position
      //--- output information about the position
      PrintFormat("#%I64u %s  %s  %.2f  %s  sl: %s  tp: %s  [%I64d]",
                  position_ticket,
                  position_symbol,
                  EnumToString(type),
                  volume,
                  DoubleToString(PositionGetDouble(POSITION_PRICE_OPEN),digits),
                  DoubleToString(sl,digits),
                  DoubleToString(tp,digits),
                  magic);
      //--- if the MagicNumber matches, Stop Loss and Take Profit are not defined
      // if sl distance is far
      MqlTick latest_price;   // To get the latest price
      SymbolInfoTick(tradingSymbol, latest_price);
      double sl_distance = MathAbs(latest_price.ask - entry_price);
      bool is_sl_far_from_be = sl_distance > 0.1;

      if(magic==EXPERT_MAGIC)
        {
         //START update SL when not set

         //double sym_digit = SymbolInfoInteger(tradingSymbol, SYMBOL_DIGITS);
         //double pips_to_sl = distance_to_trigger_be * Point();
         //Print("pips_to_sl: ", pips_to_sl);
         //int TotalPositions = PositionsTotal();
         //Print("TotalPositions: ", TotalPositions);

         ENUM_POSITION_TYPE postition_type = PositionGetInteger(POSITION_TYPE);
         // START finding SL when SELL
         //Print("entry_price: ", entry_price);


         if(postition_type == POSITION_TYPE_SELL && entry_price - latest_price.bid > distance_to_trigger_be)
           {
            new_stop_loss = entry_price - add_pip_to_sl;
            new_tp = tp;
            //TakeProfit = new_stop_loss - (TPAwayFromEntry - DistanceToTriggerBE);
            //TakeProfit = new_stop_loss - TPAwayFromEntry;
            shouldRequestChange = true;
            Print("SELL Side");
            Print("Changed : new_stop_loss to new:::", new_stop_loss);
            Print("Changed : TAke profit to new:::", tp);
           }

         // END finding SL when SELL

         // START finding SL when BUY
         // latest_price.ask is normal higher than latest_price.bid
         // -> trader has to be bough at higher price
         if(postition_type == POSITION_TYPE_BUY && latest_price.ask - entry_price > distance_to_trigger_be)
           {
            new_stop_loss = entry_price + add_pip_to_sl;
            new_tp = tp;
            //TakeProfit = new_stop_loss + (TPAwayFromEntry - DistanceToTriggerBE);
            //TakeProfit = new_stop_loss + TPAwayFromEntry;
            shouldRequestChange = true;
            Print("BUY Side");
            Print("Changed : new_stop_loss to new:::", new_stop_loss);
            Print("Changed : TAke profit to new:::", tp);
           }
         // END finding SL when BUY
         if(shouldRequestChange)
           {
            Print("DESIRE: latest_price.ask ", latest_price.ask);
            Print("DESIRE: latest_price.bid ", latest_price.bid);
            Print("DESIRE: postition_type ", postition_type);
            Print("DESIRE: entry_price", entry_price);
            Print("DESIRE: old sl is::", sl);
            Print("DESIRE: new_stop_loss is::", new_stop_loss);
            Print("DESIRE: new_tp is::", new_tp);
            Print("shouldRequestChange,", shouldRequestChange);



            double price=PositionGetDouble(POSITION_PRICE_OPEN);
            double bid=SymbolInfoDouble(position_symbol,SYMBOL_BID);
            double ask=SymbolInfoDouble(position_symbol,SYMBOL_ASK);
            int    stop_level=(int)SymbolInfoInteger(position_symbol,SYMBOL_TRADE_STOPS_LEVEL);
            Print("stop level", stop_level);
            double price_level;
            //--- if the minimum allowed offset distance in points from the current close price is not set
            if(stop_level<=0)
               stop_level=-999999; // set the offset distance of 150 points from the current close price
            else
               stop_level+=999999; // set the offset distance to (SYMBOL_TRADE_STOPS_LEVEL + 50) points for reliability
            stop_level = 9999999999;
            Print("new stop level", stop_level);
            //--- calculation and rounding of the Stop Loss and Take Profit values
            price_level=stop_level*SymbolInfoDouble(position_symbol,SYMBOL_POINT);
            if(type==POSITION_TYPE_BUY)
              {
               sl=NormalizeDouble(bid-price_level,digits);
               tp=NormalizeDouble(bid+price_level,digits);
               //  sl = 1920;
               //tp = 2020;
              }
            else
              {
               sl=NormalizeDouble(ask+price_level,digits);
               tp=NormalizeDouble(ask-price_level,digits);
               //     sl = 2010;
               //tp = 1927;
              }



            //--- zeroing the request and result values
            ZeroMemory(request);
            ZeroMemory(result);
            //--- setting the operation parameters
            request.action  =TRADE_ACTION_SLTP; // type of trade operation
            request.position=position_ticket;   // ticket of the position
            request.symbol=position_symbol;     // symbol
            request.sl      =new_stop_loss;                // Stop Loss of the position
            request.tp      =new_tp;
            request.magic=EXPERT_MAGIC;         // MagicNumber of the position
            //--- output information about the modification
            PrintFormat("Modify #%I64d %s %s",position_ticket,position_symbol,EnumToString(type));
            //--- send the request
            if(shouldRequestChange && PositionGetDouble(POSITION_SL) != sl)
              {
               Print("requiest change SL", new_stop_loss);
               Print("requiest change TP", new_tp);
               if(!OrderSend(request,result))
                 {
                  Print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG");
                  Print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG");
                  Print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG");
                  Print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG");
                  Print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG");
                  PrintFormat("OrderSend error %d",GetLastError());  // if unable to send the request, output the error code
                 }


               //--- information about the operation
               PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
              }
            //END update SL when not set
           }


        }
     }
  }
//+------------------------------------------------------------------+
//| Tester: per-year P&L + robustness score (written to Common\Files)|
//+------------------------------------------------------------------+
double OnTester()
  {
   double deposit      = TesterStatistics(STAT_INITIAL_DEPOSIT);
   double netProfit    = TesterStatistics(STAT_PROFIT);
   double profitFactor = TesterStatistics(STAT_PROFIT_FACTOR);
   double trades       = TesterStatistics(STAT_TRADES);
   double maxDDpct     = TesterStatistics(STAT_EQUITYDD_PERCENT);
   double expectancy   = TesterStatistics(STAT_EXPECTED_PAYOFF);

//--- realized profit per calendar year, from closing deals
//--- also dump one row per closing deal for offline trade-level analysis
   int    yearNum[];
   double yearNet[];
   int fdeals = FileOpen("catba_trades.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fdeals!=INVALID_HANDLE)
      FileWrite(fdeals,"close_time","type","volume","price","profit","swap","commission","reason");
   HistorySelect(0, TimeCurrent());
   int totalDeals = HistoryDealsTotal();
   for(int i=0; i<totalDeals; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket==0)
         continue;
      if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue; // only closing deals realize P&L
      datetime t = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      MqlDateTime mdt;
      TimeToStruct(t, mdt);
      double p = HistoryDealGetDouble(ticket, DEAL_PROFIT)
                 + HistoryDealGetDouble(ticket, DEAL_SWAP)
                 + HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      if(fdeals!=INVALID_HANDLE)
         FileWrite(fdeals,
                   TimeToString(t, TIME_DATE|TIME_MINUTES),
                   (HistoryDealGetInteger(ticket, DEAL_TYPE)==DEAL_TYPE_BUY ? "closebuy" : "closesell"),
                   HistoryDealGetDouble(ticket, DEAL_VOLUME),
                   HistoryDealGetDouble(ticket, DEAL_PRICE),
                   HistoryDealGetDouble(ticket, DEAL_PROFIT),
                   HistoryDealGetDouble(ticket, DEAL_SWAP),
                   HistoryDealGetDouble(ticket, DEAL_COMMISSION),
                   (int)HistoryDealGetInteger(ticket, DEAL_REASON));
      int idx=-1;
      for(int k=0; k<ArraySize(yearNum); k++)
         if(yearNum[k]==mdt.year) { idx=k; break; }
      if(idx<0)
        {
         idx=ArraySize(yearNum);
         ArrayResize(yearNum, idx+1);
         ArrayResize(yearNet, idx+1);
         yearNum[idx]=mdt.year;
         yearNet[idx]=0.0;
        }
      yearNet[idx]+=p;
     }
   if(fdeals!=INVALID_HANDLE)
      FileClose(fdeals);

//--- robustness metrics
   int nYears=ArraySize(yearNum), posYears=0;
   double worstYear=0.0;
   for(int k=0; k<nYears; k++)
     {
      if(yearNet[k]>0) posYears++;
      if(yearNet[k]<worstYear) worstYear=yearNet[k];
     }
   double posFrac      = (nYears>0)   ? (double)posYears/nYears : 0.0;
   double netPct       = (deposit>0)  ? netProfit/deposit*100.0 : 0.0;
   double worstYearPct = (deposit>0)  ? worstYear/deposit*100.0 : 0.0; // <= 0

//--- score: reward total return AND consistency; punish worst year + drawdown
   double score = netPct*posFrac - 3.0*(-worstYearPct) - 1.0*maxDDpct;
   if(trades < 30)
      score = -1000.0; // too few trades to be trustworthy

//--- dump to Common\Files\catba_results.csv
   int fh = FileOpen("catba_results.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh!=INVALID_HANDLE)
     {
      FileWrite(fh,"metric","value");
      FileWrite(fh,"deposit",deposit);
      FileWrite(fh,"netProfit",netProfit);
      FileWrite(fh,"netPct",netPct);
      FileWrite(fh,"profitFactor",profitFactor);
      FileWrite(fh,"trades",(int)trades);
      FileWrite(fh,"maxDDpct",maxDDpct);
      FileWrite(fh,"expectancy",expectancy);
      FileWrite(fh,"nYears",nYears);
      FileWrite(fh,"posYears",posYears);
      FileWrite(fh,"posFrac",posFrac);
      FileWrite(fh,"worstYearPct",worstYearPct);
      FileWrite(fh,"score",score);
      FileWrite(fh,"YEARS","");
      for(int k=0; k<nYears; k++)
         FileWrite(fh, yearNum[k], yearNet[k]);
      FileClose(fh);
     }
   return score;
  }
//+------------------------------------------------------------------+
