// TODO:  pass value by reference
https://www.mql5.com/en/forum/130174/page2

void my_function(int& output_1, int& output_2)
{
        //....
        //Set values to output variables
        output_1 = 5;
        output_2 = 10;
}

//Example of function usage
int a, b;
my_function(a, b);
Print(a,":",b);

// TODO: get previous days close and open price
double price;
datetime prev_day;
int shift;

// Get previous trading day
prev_day = iTime(_Symbol, PERIOD_D1, 1);

// Get shift for previous trading day's close price
shift = iBarShift(_Symbol, PERIOD_D1, prev_day);

// Get previous trading day's close price
price = iClose(_Symbol, PERIOD_D1, shift);

// Print previous trading day's close price
Print("Previous trading day's close price: ", price);