//+------------------------------------------------------------------+
//|                                                          QPT.mq5 |
//|                                                         Hoang Le |
//|                             https://www.mql5.com/en/users/ghoang |
//+------------------------------------------------------------------+
//--- input parameters
input string   trade_symbol="GBPJPY+";
input int      ema1=20;
input int      ema2=0;
input int      ema3=100;
input int      ema4=200;
input int      reward=1;
// if disable only using M15
input int      htf_check_bars=20;
input bool     using_htf_bias=true;
input string   htf="H4";
input bool     trade_in_transition_bias=true;
input string   entry_time_frame="M15"; // using to flip to m5 tf as example


bool is_bias_in_transition=false;


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
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
   int checkBars= htf_check_bars; 
   int move1;
   int move2;
   move1=getmove(MODE_HIGH,checkBars,0);
   move2=getmove(MODE_HIGH,checkBars,move1+1);
   ObjectDelete(0,"topLine");
   ObjectCreate(0,"topLine",OBJ_TREND,0,iTime(Symbol(),Period(),move2),iHigh(Symbol(),Period(),move2),iTime(Symbol(),Period(),move1),iHigh(Symbol(),Period(),move1));
   ObjectSetInteger(0,"topLine",OBJPROP_COLOR,clrRed);
   ObjectSetInteger(0,"topLine",OBJPROP_WIDTH,3);
   ObjectSetInteger(0,"topLine",OBJPROP_RAY_RIGHT,true);
   move1=getmove(MODE_LOW,checkBars,0);
   move2=getmove(MODE_LOW,checkBars,move1+1);
   ObjectDelete(0,"bottomLine");
   ObjectCreate(0,"bottomLine",OBJ_TREND,0,iTime(Symbol(),Period(),move2),iLow(Symbol(),Period(),move2),iTime(Symbol(),Period(),move1),iLow(Symbol(),Period(),move1));
   ObjectSetInteger(0,"bottomLine",OBJPROP_COLOR,clrGreen);
   ObjectSetInteger(0,"bottomLine",OBJPROP_WIDTH,3);
   ObjectSetInteger(0,"bottomLine",OBJPROP_RAY_RIGHT,true);
  }
//+------------------------------------------------------------------+

int getmove(int move, int count, int startPos)
  {
   if(move!=MODE_HIGH && move!=MODE_LOW)
      return (-1);
   int currentBar=startPos;
   int moveReturned=getNextMove(move,count*2+1,currentBar-count);
   while(moveReturned!=currentBar)
     {
      currentBar=getNextMove(move,count,currentBar+1);
      moveReturned=getNextMove(move,count*2+1,currentBar-count);
     }
   return(currentBar);
  }
  
int getNextMove(int move, int count, int startPos)
  {
   if(startPos<0)
     {
      count +=startPos;
      startPos =0;
     }
   return((move==MODE_HIGH)?
          iHighest(Symbol(),Period(),(ENUM_SERIESMODE)move,count,startPos):
          iLowest(Symbol(),Period(),(ENUM_SERIESMODE)move,count,startPos));
  }