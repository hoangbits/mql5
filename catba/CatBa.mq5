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
input double   riskPercentPerTrade=0.5;
input bool     useRiskPercentPerTrade=true;
input int      emaPeriod=13;   // 13 > default 8 on GBPJPY (H17 walk-forward+PBO;
                               // GBPJPY-specific, cross-pair failed — forward-confirm)
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
//--- VALIDATED sizing: size on a FIXED reference stop (equity-proportional,
//--- independent of the trade's SL) — avoids the inverse-SL-distance poison
//--- that caused the -76% decade (research H12/H12b). Scales safely with any
//--- account size. When true, riskPercentPerTrade is risked assuming refStopPips.
input bool     useFixedRefStopSizing=true;
input double   refStopPips=70.0;
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
//--- break-even management audit (research H9): off switch + ATR trigger
input bool     useBreakEven=true;
input double   beAtrMult=0.3;   // >0: BE trigger = mult*ATR(14,D1) instead of DistanceToTriggerBE (validated H9)
//--- structural regime gate: only trade when yesterday's D1 ADX(14) is
//--- above threshold, i.e. enough directional structure (research H14)
input bool     useAdxGate=false;
input double   adxThreshold=20.0;
input double   minPipsRequiredFromLastWeek=0.0;
input double   addPipsToEMA=0.11;
//--- loss-mode filter: skip entries whose pivot-based SL is closer than this
//--- many pips (tight-SL setups win only ~38% — loss_analysis). 0 = off.
input double   minStopPips=30.0;
input double   DistanceToTriggerBE=0.72;
input double   add_pip_to_sl=0.2;
//--- #1 EXIT experiment: trail the SL by ATR(14,D1) to LET WINNERS RUN instead
//--- of capping at the fixed pivot TP. Directly exploits the trend-tail edge
//--- (payoff is only ~0.95 because the fixed TP caps winners). Ratchets only
//--- in favour, never backward. letWinnersRun drops the hard TP so the trade
//--- exits solely on the trail — the true let-it-run test.
input bool     useTrailing=false;
input double   trailAtrMult=3.0;
input bool     letWinnersRun=false;
//--- how often (minutes) to run break-even management. NOTE: this was
//--- previously a latent bug (used the 12-min entry cadence); making it
//--- explicit. Slower checks outperform 1-min (don't lock BE too eagerly).
input int      checkSlEveryMinutes=12;
//--- gate diagnostic logging; keep false in tester/live to avoid GB-scale
//--- Experts logs (this EA prints per-check). Turn on only for debugging.
input bool     verboseLog=false;

double distance_to_trigger_be = DistanceToTriggerBE;
int EXPERT_MAGIC = 042024;
double g_initial_equity = 0.0;   // captured in OnInit; base for riskOnInitialDeposit

datetime previousRange = 0;
datetime previous_check_sl_range = 0;
//--- related to EMA
int    emaHandle;
double MA_Buffer[];
//--- daily ATR for H8b exits
int    atrHandle;
double ATR_Buffer[];
//--- daily ADX for H14 regime gate
int    adxHandle;
double ADX_Buffer[];




//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
//--- todo copy it to ontick later
   if(verboseLog) Print("-------------------on init start-------------------");
   g_initial_equity = AccountInfoDouble(ACCOUNT_EQUITY);
// TimeCurrent() (which returns the current time in seconds since 1970)
   previousRange = TimeCurrent() / (60 * checkEveryMinutes);
   previous_check_sl_range = TimeCurrent() / (60 * checkSlEveryMinutes);

   emaHandle = iMA(tradingSymbol,PERIOD_H1,emaPeriod,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(MA_Buffer,true);
   atrHandle = iATR(tradingSymbol,PERIOD_D1,14);
   ArraySetAsSeries(ATR_Buffer,true);
   adxHandle = iADX(tradingSymbol,PERIOD_D1,14);
   ArraySetAsSeries(ADX_Buffer,true);

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

   datetime current_check_sl_range = TimeCurrent() / (60 * checkSlEveryMinutes);

   if(current_check_sl_range != previous_check_sl_range)
     {
      update_sl_to_be();
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
//--- H14: require directional structure (yesterday's completed D1 ADX)
   if(useAdxGate)
     {
      if(CopyBuffer(adxHandle,0,1,1,ADX_Buffer)!=1)
         return;
      if(ADX_Buffer[0] < adxThreshold)
         return;
     }
   string todayBias = get_daily_bias();
//string todayBias = get_previous_week_bias();
   if(verboseLog) Print("main::todayBias: ", todayBias);
// can place max 2 trade per day
   if(!isAlreadyPlaceATradeToday() && todayBias != "NOBIAS"
      && (!useTrailing || CountOpenPositions()==0))   // #1: no stacking while a runner is open
     {
      //--- Get the current Bid price
      double currentBid = SymbolInfoDouble(tradingSymbol, SYMBOL_BID);
      //--- Get the current Ask price
      double currentAsk = SymbolInfoDouble(tradingSymbol, SYMBOL_ASK);
      if(verboseLog) Print("handle_new_tick::Current Bid: ", currentBid);
      if(verboseLog) Print("handle_new_tick::Current Ask: ", currentAsk);

      if(CopyBuffer(emaHandle,0,0,2,MA_Buffer)!=2)
         return;
      //--- MA_Buffer[0] is current candle EMA
      if(verboseLog) Print("handle_new_tick::MA_Buffer[0]: ", MA_Buffer[0]);
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
      if(verboseLog) Print("vhandle_new_tick:: R1: ", vR1);
      if(verboseLog) Print("handle_new_tick:: vS1: ", vS1);
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
               if(minStopPips <= 0.0 || (currentAsk - sl) >= minStopPips*0.01)
                  place_trade(ORDER_TYPE_BUY, sl, tp);
              }
            else
              {
               if(verboseLog) Print("handle_new_tick:: looking for BUY but currentASL is not < EMA9 hourly ");
              }

           }
         else
           {
            // TODO: might not need handle this
            if(verboseLog) Print("not handle buy both side yet");
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
                  if(verboseLog) Print("handle_new_tick::START SELL as currentBid > ema9_hourly: ", currentAsk > MA_Buffer[0]);
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
                  if(minStopPips <= 0.0 || (sl - currentBid) >= minStopPips*0.01)
                     place_trade(ORDER_TYPE_SELL, sl, tp);
                 }
               else
                 {
                  if(verboseLog) Print("handle_new_tick:: looking for sell but currentbid is not > EMA9 hourly ");
                 }
              }
            else
              {
               if(verboseLog) Print("not handle SELL both side yet");
               // TODO:
              }

           }

     }
   else
     {
      if(verboseLog) Print("Done for the day, Trade already placed!");
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

   if(verboseLog) Print("get_daily_bias:: prev_day ", prev_day, " bias value: ", bias);
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

   if(verboseLog) Print("get_previous_week_bias:: prev_week ", prev_week, " bias value: ", bias);
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
   if(verboseLog) Print("total_trade_placed_today:: today_start_time:", today_start_time," total_trade_placed_today: ", total_trade_placed_today);
   return total_trade_placed_today;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
//--- #1: count this EA's currently OPEN positions. The daily guard only blocks
//--- a 2nd entry on the SAME day; with trailing/let-winners-run a position can
//--- linger for weeks, so without this the EA would STACK positions every day.
int CountOpenPositions()
  {
   int c=0;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong tk=PositionGetTicket(i);
      if(tk>0 && PositionGetInteger(POSITION_MAGIC)==EXPERT_MAGIC
         && PositionGetString(POSITION_SYMBOL)==tradingSymbol)
         c++;
     }
   return c;
  }

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

   if(verboseLog) Print("isAlreadyPlaceATradeToday::today_start_time value:", today_start_time);
   if(verboseLog) Print("isAlreadyPlaceATradeToday::is placed trade Today: ", tradePlacedToday);
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
      if(verboseLog) Print("CalculateLotSize:: invalid inputs slDistance=", slDistance,
            " tickSize=", tickSize, " tickValue=", tickValue);
      return 0.0;
     }

//--- distance used for SIZING. Default uses a FIXED reference stop so the
//--- lot does NOT scale inversely with the trade's SL (the validated fix);
//--- the ACTUAL slDistance is still used for the order's stop-loss.
   double point       = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int    digits      = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double pip         = ((digits == 3 || digits == 5) ? 10.0 : 1.0) * point;
   double sizingDist  = useFixedRefStopSizing ? (refStopPips * pip) : slDistance;

//--- money lost on 1.0 lot over the sizing distance.
//--- tickValue is already in the deposit currency, so no manual FX conversion is needed.
   double lossPerLot = (sizingDist / tickSize) * tickValue;
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
      if(verboseLog) Print("CalculateLotSize:: risk-based lot below min (", volMin,
            ") -> using min; actual risk will exceed the ", riskPerTrade*100, "% target");
      lots = volMin;
     }
   if(lots > volMax)
      lots = volMax;
   lots = NormalizeDouble(lots, 2);

   if(verboseLog) Print("CalculateLotSize:: equity=", AccountInfoDouble(ACCOUNT_EQUITY),
         " risk=", riskPerTrade, " riskAmount=", riskAmount,
         " slDistance=", slDistance, " lossPerLot=", lossPerLot, " lots=", lots);
   return lots;
  }




//+------------------------------------------------------------------+
//| Pick an order filling mode the symbol actually supports          |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode(string symbol)
  {
   int modes = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
   if((modes & SYMBOL_FILLING_IOC) != 0)
      return ORDER_FILLING_IOC;
   if((modes & SYMBOL_FILLING_FOK) != 0)
      return ORDER_FILLING_FOK;
   return ORDER_FILLING_RETURN;
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
   if(useRiskPercentPerTrade && riskPercentPerTrade > 0.0)
     {
      //--- Calculate lot size for riskPercentPerTrade% risk
      trade_lot_size = CalculateLotSize(tradingSymbol, entry_price, new_stop_lossPrice, riskPercentPerTrade/100);
      if(verboseLog) Print("Lot size for riskPercentPerTrade:", riskPercentPerTrade,"% risk: ", trade_lot_size);
     }
   if(verboseLog) Print("lotSize Placing: ", trade_lot_size);



   request.action = TRADE_ACTION_DEAL;
   request.symbol = tradingSymbol;
   request.volume = trade_lot_size;
   request.type = orderType;
   request.type_filling = GetFillingMode(tradingSymbol);
   request.price = entry_price;

   if(verboseLog) Print("place_trade::", orderType,"  at price:", request.price);
   if(verboseLog) Print("place_trade::Stop Loss set at:", new_stop_lossPrice);
   if(verboseLog) Print("place_trade::Take Profit set at:", takeProfitPrice);
   request.deviation = 10;
   request.magic = EXPERT_MAGIC;

   request.sl = new_stop_lossPrice;
   request.tp = letWinnersRun ? 0.0 : takeProfitPrice;   // #1: drop hard TP, exit on trail


   if(verboseLog) Print(SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE));

//--- send the request
   if(!OrderSend(request,result))
     {
      if(verboseLog) PrintFormat("OrderSend error %d",GetLastError());     // if unable to send the request, output the error code
     }

//--- information about the operation
//--- when DEBUG also check Journal tab(beside of expert tab.)
   if(verboseLog) PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
   if(verboseLog) Print("place_trade::result.comment: ",result.comment);
   if(verboseLog) Print("place_trade::result.request_id: ",result.request_id);
   if(verboseLog) Print("place_trade11::result.retcode_external", result.retcode_external);

  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void update_sl_to_be()
  {
   if(!useBreakEven)
      return;
//--- H9: optionally scale the BE trigger with daily ATR
   if(beAtrMult > 0.0)
     {
      if(CopyBuffer(atrHandle,0,1,1,ATR_Buffer)==1 && ATR_Buffer[0] > 0.0)
         distance_to_trigger_be = beAtrMult * ATR_Buffer[0];
     }
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
      if(verboseLog) Print("OILDDDDDDDDDDDD SL ", sl);
      double shouldRequestChange = false;

      ENUM_POSITION_TYPE type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);  // type of the position
      //--- output information about the position
      if(verboseLog) PrintFormat("#%I64u %s  %s  %.2f  %s  sl: %s  tp: %s  [%I64d]",
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
            if(verboseLog) Print("SELL Side");
            if(verboseLog) Print("Changed : new_stop_loss to new:::", new_stop_loss);
            if(verboseLog) Print("Changed : TAke profit to new:::", tp);
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
            if(verboseLog) Print("BUY Side");
            if(verboseLog) Print("Changed : new_stop_loss to new:::", new_stop_loss);
            if(verboseLog) Print("Changed : TAke profit to new:::", tp);
           }
         // END finding SL when BUY

         //--- #1: ATR trailing ratchet (let winners run). Once price has moved
         //--- in favour, trail SL to price -/+ trailAtrMult*ATR, only tightening.
         if(useTrailing && trailAtrMult > 0.0)
           {
            double atrNow = 0.0;
            if(CopyBuffer(atrHandle,0,1,1,ATR_Buffer)==1) atrNow = ATR_Buffer[0];
            if(atrNow > 0.0)
              {
               double trail = trailAtrMult * atrNow;
               double cur_sl = shouldRequestChange ? new_stop_loss : sl;
               if(postition_type == POSITION_TYPE_BUY)
                 {
                  double cand = latest_price.bid - trail;
                  if(cand < latest_price.bid && (cur_sl <= 0.0 || cand > cur_sl))
                    { new_stop_loss = cand; new_tp = tp; shouldRequestChange = true; }
                 }
               else
                  if(postition_type == POSITION_TYPE_SELL)
                    {
                     double cand = latest_price.ask + trail;
                     if(cand > latest_price.ask && (cur_sl <= 0.0 || cand < cur_sl))
                       { new_stop_loss = cand; new_tp = tp; shouldRequestChange = true; }
                    }
              }
           }

         if(shouldRequestChange)
           {
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
            if(verboseLog) PrintFormat("Modify #%I64d %s %s",position_ticket,position_symbol,EnumToString(type));
            //--- send the request only if the stop actually moves
            if(shouldRequestChange && PositionGetDouble(POSITION_SL) != new_stop_loss)
              {
               if(verboseLog) Print("request change SL ", new_stop_loss, " TP ", new_tp);
               if(!OrderSend(request,result))
                  if(verboseLog) PrintFormat("update_sl_to_be OrderSend error %d",GetLastError());


               //--- information about the operation
               if(verboseLog) PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
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

//--- RICH per-trade dump (entry paired with exit) for loss-mode analysis
   HistorySelect(0, TimeCurrent());
   int td = HistoryDealsTotal();
   long     inPos[];
   datetime inTime[];
   double   inPrice[], inSL[], inTP[];
   int      inType[];
   for(int i=0; i<td; i++)
     {
      ulong tk = HistoryDealGetTicket(i);
      if(tk==0 || HistoryDealGetInteger(tk,DEAL_ENTRY)!=DEAL_ENTRY_IN)
         continue;
      int n = ArraySize(inPos);
      ArrayResize(inPos,n+1); ArrayResize(inTime,n+1); ArrayResize(inPrice,n+1);
      ArrayResize(inSL,n+1); ArrayResize(inTP,n+1); ArrayResize(inType,n+1);
      inPos[n]   = HistoryDealGetInteger(tk,DEAL_POSITION_ID);
      inTime[n]  = (datetime)HistoryDealGetInteger(tk,DEAL_TIME);
      inPrice[n] = HistoryDealGetDouble(tk,DEAL_PRICE);
      inType[n]  = (int)HistoryDealGetInteger(tk,DEAL_TYPE); // 0 buy(long) 1 sell(short)
      ulong ord  = HistoryDealGetInteger(tk,DEAL_ORDER);
      inSL[n]    = HistoryOrderGetDouble(ord,ORDER_SL);
      inTP[n]    = HistoryOrderGetDouble(ord,ORDER_TP);
     }
   int fx = FileOpen("catba_tradesx.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fx!=INVALID_HANDLE)
     {
      FileWrite(fx,"entry_time","exit_time","side","entry","exit","sl","tp","profit","reason","hold_min");
      for(int i=0; i<td; i++)
        {
         ulong tk = HistoryDealGetTicket(i);
         if(tk==0 || HistoryDealGetInteger(tk,DEAL_ENTRY)!=DEAL_ENTRY_OUT)
            continue;
         long pid = HistoryDealGetInteger(tk,DEAL_POSITION_ID);
         int mi=-1;
         for(int k=ArraySize(inPos)-1; k>=0; k--)
            if(inPos[k]==pid) { mi=k; break; }
         if(mi<0) continue;
         datetime xt = (datetime)HistoryDealGetInteger(tk,DEAL_TIME);
         double   xp = HistoryDealGetDouble(tk,DEAL_PRICE);
         double   pf = HistoryDealGetDouble(tk,DEAL_PROFIT)
                       + HistoryDealGetDouble(tk,DEAL_SWAP)
                       + HistoryDealGetDouble(tk,DEAL_COMMISSION);
         FileWrite(fx,
                   TimeToString(inTime[mi],TIME_DATE|TIME_MINUTES),
                   TimeToString(xt,TIME_DATE|TIME_MINUTES),
                   (inType[mi]==0 ? "buy" : "sell"),
                   inPrice[mi], xp, inSL[mi], inTP[mi], pf,
                   (int)HistoryDealGetInteger(tk,DEAL_REASON),   // 4=SL 5=TP
                   (int)((xt-inTime[mi])/60));
        }
      FileClose(fx);
     }
   return score;
  }
//+------------------------------------------------------------------+
