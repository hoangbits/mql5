//+------------------------------------------------------------------+
//|                                                       HSL1.1.mq5 |
//|                                                            Hoang |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Hoang"
#property link      "https://www.mql5.com"
#property version   "1.17"

//--- input parameters
#define EXPERT_MAGIC = 123456
input double      DistanceToTriggerBE=3;
input double      MinProfitDistance=0.1;
input double      DistanceToTriggerMinProfit=3.1;
//input double      TPAwayFromEntry=10;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
   
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
  
  
#define EXPERT_MAGIC 123456  // MagicNumber of the expert
//+------------------------------------------------------------------+
//| Modification of Stop Loss and Take Profit of position            |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+  
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
// write mql5 code to set SL to entry price of all current position when current price of XAUUSD move more than 20pips.
// write mql5 code to set SL to entry price of all current position when current price of XAUUSD move more than 20pips.



//---1.0+
static double StopLoss;
static double TakeProfit;
static bool shouldRequestChange;
//void modifySL2(ulong Ticket, double StopLoss,double TakeProfit) {
void OnTick() {
//--- declare and initialize the trade request and result of trade request
   MqlTradeRequest request;
   MqlTradeResult  result;
   int total=PositionsTotal(); // number of open positions   
//--- iterate over all open positions
   for(int i=0; i<total; i++)
     {
      //--- parameters of the order
      ulong  position_ticket=PositionGetTicket(i);// ticket of the position
      string position_symbol=PositionGetString(POSITION_SYMBOL); // symbol 
      int    digits=(int)SymbolInfoInteger(position_symbol,SYMBOL_DIGITS); // number of decimal places
      ulong  magic=PositionGetInteger(POSITION_MAGIC); // MagicNumber of the position
      double volume=PositionGetDouble(POSITION_VOLUME);    // volume of the position
      double sl=PositionGetDouble(POSITION_SL);  // Stop Loss of the position
      double tp=PositionGetDouble(POSITION_TP);  // Take Profit of the position

      shouldRequestChange = false;
      
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
    //  if(1==1) { 
      // START calculate 
      
                double XAUUSD_Price = SymbolInfoDouble(_Symbol, SYMBOL_BID);                                
                Print("_Symbol: ", _Symbol);
                //Print("XAUUSD_Price: ", XAUUSD_Price);
                //double XAUUSD_Pips = SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
                //Print("XAUUSD_Pips: ", XAUUSD_Pips);
                //double XAUUSD_PipsToSL = DistanceToTriggerBE * Point();
                //Print("XAUUSD_PipsToSL: ", XAUUSD_PipsToSL);
                //double XAUUSD_SL = 0;
                //int TotalPositions = PositionsTotal();
                 //Print("TotalPositions: ", TotalPositions);
                 ulong Ticket = PositionGetTicket(i);
                  //  if (Ticket > 0){
                        ENUM_POSITION_TYPE Type = PositionGetInteger(POSITION_TYPE);                        
                                   
                            double EntryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                            //Print("EntryPrice,", EntryPrice);
                            //double StopLoss = EntryPrice - XAUUSD_PipsToSL;
                            // handle sell
                            
                            //Print("EntryPrice: ", EntryPrice);
                            //Print("XAUUSD_Price: ", XAUUSD_Price);
                            //Print("XAUUSD_PipsToSL: ", XAUUSD_PipsToSL);
                            //Print("XAUUSD_Pips: ", XAUUSD_Pips);
                            if (Type == POSITION_TYPE_SELL && EntryPrice - XAUUSD_Price > DistanceToTriggerBE)
                            {
                                StopLoss = EntryPrice;                                                                
                                //TakeProfit = StopLoss - (TPAwayFromEntry - DistanceToTriggerBE);
                                //TakeProfit = StopLoss - TPAwayFromEntry;
                                shouldRequestChange = true;                                
                                Print("SELL Side");
                                Print("Changed : STOPLOSS to new:::", StopLoss);
                                Print("Changed : TAke profit to new:::", TakeProfit);   
                            }  
                            // START MIN profit 
                             if (Type == POSITION_TYPE_SELL && EntryPrice - XAUUSD_Price > DistanceToTriggerMinProfit)
                            {
                                StopLoss = EntryPrice - MinProfitDistance;                                                                
                                //TakeProfit = StopLoss - (TPAwayFromEntry - DistanceToTriggerBE);
                                //TakeProfit = StopLoss - TPAwayFromEntry;
                                shouldRequestChange = true;                                
                                Print("SELL Side");
                                Print("Changed : STOPLOSS to new:::", StopLoss);
                                Print("Changed : TAke profit to new:::", TakeProfit);   
                            }     
                            // END MIN profit                            
                        //end handle sell
                        
                        //start handle buy
                        if (Type == POSITION_TYPE_BUY && XAUUSD_Price - EntryPrice > DistanceToTriggerBE)
                            {
                                StopLoss = EntryPrice;                                                                  
                                //TakeProfit = StopLoss + (TPAwayFromEntry - DistanceToTriggerBE);
                                //TakeProfit = StopLoss + TPAwayFromEntry; 
                                shouldRequestChange = true;                             
                                Print("BUY Side");
                                Print("Changed : STOPLOSS to new:::", StopLoss);
                                Print("Changed : TAke profit to new:::", TakeProfit);      
                             }
                                   if (Type == POSITION_TYPE_BUY && XAUUSD_Price - EntryPrice > DistanceToTriggerMinProfit)
                            {
                                StopLoss = EntryPrice + MinProfitDistance;                                                                  
                                //TakeProfit = StopLoss + (TPAwayFromEntry - DistanceToTriggerBE);
                                //TakeProfit = StopLoss + TPAwayFromEntry; 
                                shouldRequestChange = true;                             
                                Print("BUY Side");
                                Print("Changed : STOPLOSS to new:::", StopLoss);
                                Print("Changed : TAke profit to new:::", TakeProfit);      
                             }
                        // end handle buy
                        
             //       }
      // end calcuate      
        Print(":::::::::::::START AFter CHANGED tp, sl::::::::::::::::::::");
        Print("DESIRE: STOPLOSS is::", StopLoss);        
        Print("DESIRE: TakeProfit is::", TakeProfit);
        Print("shouldRequestChange,", shouldRequestChange);
        Print(":::::::::::::END AFter CHANGED tp, sl::::::::::::::::::::");
         //--- calculate the current price levels
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
         
               //modify SL, tp
           sl = StopLoss;
           tp=TakeProfit;
              //end modify Sl tp
           
           
         Print("new sl", sl);
         //--- zeroing the request and result values
         ZeroMemory(request);
         ZeroMemory(result);
         //--- setting the operation parameters
         request.action  =TRADE_ACTION_SLTP; // type of trade operation
         request.position=position_ticket;   // ticket of the position
         request.symbol=position_symbol;     // symbol 
         request.sl      =sl;                // Stop Loss of the position
         request.tp      =tp; 
         request.magic=EXPERT_MAGIC;         // MagicNumber of the position
         //--- output information about the modification
         PrintFormat("Modify #%I64d %s %s",position_ticket,position_symbol,EnumToString(type));
         //--- send the request
         if(shouldRequestChange && PositionGetDouble(POSITION_SL) != sl ){
            Print("requiest change SL", sl);
            Print("requiest change TP", tp);
            if(!OrderSend(request,result))
            PrintFormat("OrderSend error %d",GetLastError());  // if unable to send the request, output the error code
            //--- information about the operation   
            PrintFormat("retcode=%u  deal=%I64u  order=%I64u",result.retcode,result.deal,result.order);
         }
         
        }
     //}
  }
  
