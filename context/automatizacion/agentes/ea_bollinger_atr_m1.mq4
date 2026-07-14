//+------------------------------------------------------------------+
//| EA_Bollinger_ATR_M1.mq4                                          |
//| QuantumHive Algorithmic Trading                                  |
//| EA M1 con Bollinger (40, 4.0) y ATR (7) - Doble entrada          |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property version   "1.00"
#property strict

//--- Parámetros de entrada
input int    BB_Period = 40;           // Período Bandas Bollinger
input double BB_Deviation = 4.0;       // Desviación Bandas Bollinger
input int    ATR_Period = 7;           // Período ATR
input double LotSize = 0.01;           // Tamaño del lote
input int    MagicNumber = 123456;     // Número mágico
input int    Slippage = 3;              // Deslizamiento máximo
input double StopLoss_ATR_Mult = 2.0;  // Multiplicador ATR para Stop Loss
input double TakeProfit_ATR_Mult = 3.0; // Multiplicador ATR para Take Profit

//--- Variables globales
double BB_Upper, BB_Lower, BB_Middle;
double ATR_Value;
int ticket_middle = -1;
int ticket_extreme = -1;
bool first_operation_closed = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("EA Bollinger + ATR M1 iniciado");
   Print("BB: ", BB_Period, " períodos, desviación: ", BB_Deviation);
   Print("ATR: ", ATR_Period, " períodos");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("EA Bollinger + ATR M1 detenido");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Verificar si estamos en una nueva barra
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(Symbol(), PERIOD_M1, 0);
   
   if(currentBarTime == lastBarTime)
      return;
   
   lastBarTime = currentBarTime;
   
   // Calcular indicadores
   CalculateIndicators();
   
   // Verificar operaciones existentes
   CheckOperations();
   
   // Lógica de entrada
   if(ticket_middle == -1 && ticket_extreme == -1)
   {
      // No hay operaciones abiertas, buscar entradas
      CheckEntrySignals();
   }
   else if(ticket_middle != -1 && ticket_extreme != -1)
   {
      // Ambas operaciones abiertas, verificar si se cerró alguna
      CheckClosedOperations();
   }
   else
   {
      // Una operación abierta, verificar si se cerró para poner BE en la otra
      CheckClosedOperations();
   }
}

//+------------------------------------------------------------------+
//| Calcular indicadores                                               |
//+------------------------------------------------------------------+
void CalculateIndicators()
{
   // Bandas de Bollinger
   BB_Upper = iBands(Symbol(), PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE, MODE_UPPER, 1);
   BB_Lower = iBands(Symbol(), PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE, MODE_LOWER, 1);
   BB_Middle = iBands(Symbol(), PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE, MODE_MAIN, 1);
   
   // ATR
   ATR_Value = iATR(Symbol(), PERIOD_M1, ATR_Period, 1);
}

//+------------------------------------------------------------------+
//| Verificar señales de entrada                                      |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
   double close = iClose(Symbol(), PERIOD_M1, 1);
   double open = iOpen(Symbol(), PERIOD_M1, 1);
   double high = iHigh(Symbol(), PERIOD_M1, 1);
   double low = iLow(Symbol(), PERIOD_M1, 1);
   
   // Determinar dirección basado en la posición del cierre
   bool bullish = close > BB_Middle;
   bool bearish = close < BB_Middle;
   
   if(bullish)
   {
      // Señal alcista
      // Entrada 1: Banda media (cuando el precio cruza hacia arriba)
      if(open < BB_Middle && close > BB_Middle)
      {
         double sl = close - (ATR_Value * StopLoss_ATR_Mult);
         double tp = close + (ATR_Value * TakeProfit_ATR_Mult);
         ticket_middle = OpenOrder(OP_BUY, LotSize, sl, tp, "BB Middle Buy");
         Print("Entrada 1: Banda Media BUY - Ticket: ", ticket_middle);
         
         // Entrada 2: Banda extrema superior
         if(ticket_middle != -1)
         {
            double sl2 = close - (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close + (ATR_Value * TakeProfit_ATR_Mult);
            ticket_extreme = OpenOrder(OP_BUY, LotSize, sl2, tp2, "BB Extreme Buy");
            Print("Entrada 2: Banda Extrema BUY - Ticket: ", ticket_extreme);
         }
      }
   }
   else if(bearish)
   {
      // Señal bajista
      // Entrada 1: Banda media (cuando el precio cruza hacia abajo)
      if(open > BB_Middle && close < BB_Middle)
      {
         double sl = close + (ATR_Value * StopLoss_ATR_Mult);
         double tp = close - (ATR_Value * TakeProfit_ATR_Mult);
         ticket_middle = OpenOrder(OP_SELL, LotSize, sl, tp, "BB Middle Sell");
         Print("Entrada 1: Banda Media SELL - Ticket: ", ticket_middle);
         
         // Entrada 2: Banda extrema inferior
         if(ticket_middle != -1)
         {
            double sl2 = close + (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close - (ATR_Value * TakeProfit_ATR_Mult);
            ticket_extreme = OpenOrder(OP_SELL, LotSize, sl2, tp2, "BB Extreme Sell");
            Print("Entrada 2: Banda Extrema SELL - Ticket: ", ticket_extreme);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Abrir orden                                                       |
//+------------------------------------------------------------------+
int OpenOrder(int type, double lots, double sl, double tp, string comment)
{
   double price;
   int orderType;
   
   RefreshRates();
   
   if(type == OP_BUY)
   {
      price = Ask;
      orderType = OP_BUY;
   }
   else if(type == OP_SELL)
   {
      price = Bid;
      orderType = OP_SELL;
   }
   else
   {
      return -1;
   }
   
   int ticket = OrderSend(Symbol(), orderType, lots, price, Slippage, sl, tp, comment, MagicNumber, 0, clrNONE);
   
   if(ticket < 0)
   {
      int error = GetLastError();
      Print("Error al abrir orden: ", error, " - ", ErrorDescription(error));
   }
   
   return ticket;
}

//+------------------------------------------------------------------+
//| Verificar operaciones existentes                                   |
//+------------------------------------------------------------------+
void CheckOperations()
{
   bool middle_exists = false;
   bool extreme_exists = false;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
         {
            if(StringFind(OrderComment(), "BB Middle") != -1)
            {
               ticket_middle = OrderTicket();
               middle_exists = true;
            }
            else if(StringFind(OrderComment(), "BB Extreme") != -1)
            {
               ticket_extreme = OrderTicket();
               extreme_exists = true;
            }
         }
      }
   }
   
   if(!middle_exists)
      ticket_middle = -1;
   
   if(!extreme_exists)
      ticket_extreme = -1;
}

//+------------------------------------------------------------------+
//| Verificar operaciones cerradas                                    |
//+------------------------------------------------------------------+
void CheckClosedOperations()
{
   // Verificar si la operación de banda media se cerró
   if(ticket_middle != -1)
   {
      bool middle_closed = true;
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
         {
            if(OrderTicket() == ticket_middle)
            {
               middle_closed = false;
               break;
            }
         }
      }
      
      if(middle_closed)
      {
         Print("Operación Banda Media cerrada - Ticket: ", ticket_middle);
         ticket_middle = -1;
         
         // Poner BE en la operación extrema
         if(ticket_extreme != -1)
         {
            SetBreakeven(ticket_extreme);
         }
      }
   }
   
   // Verificar si la operación extrema se cerró
   if(ticket_extreme != -1)
   {
      bool extreme_closed = true;
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
         {
            if(OrderTicket() == ticket_extreme)
            {
               extreme_closed = false;
               break;
            }
         }
      }
      
      if(extreme_closed)
      {
         Print("Operación Banda Extrema cerrada - Ticket: ", ticket_extreme);
         ticket_extreme = -1;
         
         // Poner BE en la operación de banda media
         if(ticket_middle != -1)
         {
            SetBreakeven(ticket_middle);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Poner Stop Loss en Breakeven                                      |
//+------------------------------------------------------------------+
void SetBreakeven(int ticket)
{
   if(!OrderSelect(ticket, SELECT_BY_TICKET, MODE_TRADES))
      return;
   
   double openPrice = OrderOpenPrice();
   double currentSL = OrderStopLoss();
   double currentTP = OrderTakeProfit();
   
   // Verificar si ya está en BE
   if(currentSL == openPrice)
      return;
   
   bool result;
   RefreshRates();
   
   if(OrderType() == OP_BUY)
   {
      if(Bid > openPrice)
      {
         result = OrderModify(ticket, openPrice, openPrice, currentTP, 0, clrNONE);
         if(result)
            Print("BE aplicado en orden BUY - Ticket: ", ticket);
         else
            Print("Error al aplicar BE en BUY: ", GetLastError());
      }
   }
   else if(OrderType() == OP_SELL)
   {
      if(Ask < openPrice)
      {
         result = OrderModify(ticket, openPrice, openPrice, currentTP, 0, clrNONE);
         if(result)
            Print("BE aplicado en orden SELL - Ticket: ", ticket);
         else
            Print("Error al aplicar BE en SELL: ", GetLastError());
      }
   }
}

//+------------------------------------------------------------------+
//| Descripción de error                                              |
//+------------------------------------------------------------------+
string ErrorDescription(int error)
{
   switch(error)
   {
      case 0:   return "No error";
      case 1:   return "No error, but result unknown";
      case 2:   return "Common error";
      case 3:   return "Invalid trade parameters";
      case 4:   return "Trade server busy";
      case 5:   return "Old version of terminal";
      case 6:   return "No connection with trade server";
      case 7:   return "Not enough rights";
      case 8:   return "Too frequent requests";
      case 9:   return "Operation not allowed";
      case 64:  return "Account blocked";
      case 65:  return "Invalid account";
      case 128: return "Trade timeout";
      case 129: return "Invalid price";
      case 130: return "Invalid stops";
      case 131: return "Invalid volume";
      case 132: return "Market closed";
      case 133: return "Trading disabled";
      case 134: return "Not enough money";
      case 135: return "Price changed";
      case 136: return "No prices";
      case 137: return "Broker busy";
      case 138: return "Requote";
      case 139: return "Order locked";
      case 140: return "Only long positions allowed";
      case 141: return "Too many requests";
      case 145: return "Modification denied";
      case 146: return "Trade context busy";
      case 147: return "Expirations denied";
      case 148: return "Trade too many requests";
      case 149: return "Hedge prohibited";
      case 150: return "Trading prohibited";
      default:  return "Unknown error";
   }
}
//+------------------------------------------------------------------+
