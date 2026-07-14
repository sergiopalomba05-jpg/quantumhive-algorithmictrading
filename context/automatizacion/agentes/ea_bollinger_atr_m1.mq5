//+------------------------------------------------------------------+
//| EA_Bollinger_ATR_M1.mq5                                          |
//| QuantumHive Algorithmic Trading                                  |
//| EA M1 con Bollinger (40, 4.0) y ATR (7) - Doble entrada          |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

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
CTrade trade;
int BB_Handle;
int ATR_Handle;
double BB_Buffer[];
double ATR_Buffer[];
double BB_Upper, BB_Lower, BB_Middle;
double ATR_Value;
ulong ticket_middle = 0;
ulong ticket_extreme = 0;
bool first_operation_closed = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Inicializar indicadores
   BB_Handle = iBands(_Symbol, PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   ATR_Handle = iATR(_Symbol, PERIOD_M1, ATR_Period);
   
   if(BB_Handle == INVALID_HANDLE || ATR_Handle == INVALID_HANDLE)
   {
      Print("Error al crear indicadores");
      return(INIT_FAILED);
   }
   
   // Configurar buffers
   ArraySetAsSeries(BB_Buffer, true);
   ArraySetAsSeries(ATR_Buffer, true);
   
   // Configurar trade
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   
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
   // Liberar handles
   if(BB_Handle != INVALID_HANDLE)
      IndicatorRelease(BB_Handle);
   if(ATR_Handle != INVALID_HANDLE)
      IndicatorRelease(ATR_Handle);
   
   Print("EA Bollinger + ATR M1 detenido");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Verificar si estamos en una nueva barra
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_M1, 0);
   
   if(currentBarTime == lastBarTime)
      return;
   
   lastBarTime = currentBarTime;
   
   // Calcular indicadores
   CalculateIndicators();
   
   // Verificar operaciones existentes
   CheckOperations();
   
   // Lógica de entrada
   if(ticket_middle == 0 && ticket_extreme == 0)
   {
      // No hay operaciones abiertas, buscar entradas
      CheckEntrySignals();
   }
   else if(ticket_middle != 0 && ticket_extreme != 0)
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
   // Copiar datos de Bollinger
   if(CopyBuffer(BB_Handle, 0, 0, 3, BB_Buffer) < 3)
      return;
   if(CopyBuffer(BB_Handle, 1, 0, 3, BB_Buffer) < 3)
      return;
   if(CopyBuffer(BB_Handle, 2, 0, 3, BB_Buffer) < 3)
      return;
   
   // Obtener valores
   BB_Middle = BB_Buffer[1];
   
   // Copiar datos de ATR
   if(CopyBuffer(ATR_Handle, 0, 0, 3, ATR_Buffer) < 3)
      return;
   
   ATR_Value = ATR_Buffer[1];
   
   // Obtener bandas superior e inferior
   double bb_upper[], bb_lower[];
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_lower, true);
   
   if(CopyBuffer(BB_Handle, 1, 0, 3, bb_upper) < 3)
      return;
   if(CopyBuffer(BB_Handle, 2, 0, 3, bb_lower) < 3)
      return;
   
   BB_Upper = bb_upper[1];
   BB_Lower = bb_lower[1];
}

//+------------------------------------------------------------------+
//| Verificar señales de entrada                                      |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double open = iOpen(_Symbol, PERIOD_M1, 1);
   double high = iHigh(_Symbol, PERIOD_M1, 1);
   double low = iLow(_Symbol, PERIOD_M1, 1);
   
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
         ticket_middle = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp, "BB Middle Buy");
         Print("Entrada 1: Banda Media BUY - Ticket: ", ticket_middle);
         
         // Entrada 2: Banda extrema superior
         if(ticket_middle != 0)
         {
            double sl2 = close - (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close + (ATR_Value * TakeProfit_ATR_Mult);
            ticket_extreme = OpenOrder(ORDER_TYPE_BUY, LotSize, sl2, tp2, "BB Extreme Buy");
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
         ticket_middle = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp, "BB Middle Sell");
         Print("Entrada 1: Banda Media SELL - Ticket: ", ticket_middle);
         
         // Entrada 2: Banda extrema inferior
         if(ticket_middle != 0)
         {
            double sl2 = close + (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close - (ATR_Value * TakeProfit_ATR_Mult);
            ticket_extreme = OpenOrder(ORDER_TYPE_SELL, LotSize, sl2, tp2, "BB Extreme Sell");
            Print("Entrada 2: Banda Extrema SELL - Ticket: ", ticket_extreme);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Abrir orden                                                       |
//+------------------------------------------------------------------+
ulong OpenOrder(ENUM_ORDER_TYPE type, double lots, double sl, double tp, string comment)
{
   double price;
   
   if(type == ORDER_TYPE_BUY)
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   }
   else if(type == ORDER_TYPE_SELL)
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   }
   else
   {
      return 0;
   }
   
   if(!trade.PositionOpen(_Symbol, type, lots, price, sl, tp, comment))
   {
      Print("Error al abrir orden: ", GetLastError(), " - ", trade.ResultRetcode(), " - ", trade.ResultRetcodeDescription());
      return 0;
   }
   
   return trade.ResultOrder();
}

//+------------------------------------------------------------------+
//| Verificar operaciones existentes                                   |
//+------------------------------------------------------------------+
void CheckOperations()
{
   bool middle_exists = false;
   bool extreme_exists = false;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            string comment = PositionGetString(POSITION_COMMENT);
            if(StringFind(comment, "BB Middle") != -1)
            {
               ticket_middle = PositionGetInteger(POSITION_TICKET);
               middle_exists = true;
            }
            else if(StringFind(comment, "BB Extreme") != -1)
            {
               ticket_extreme = PositionGetInteger(POSITION_TICKET);
               extreme_exists = true;
            }
         }
      }
   }
   
   if(!middle_exists)
      ticket_middle = 0;
   
   if(!extreme_exists)
      ticket_extreme = 0;
}

//+------------------------------------------------------------------+
//| Verificar operaciones cerradas                                    |
//+------------------------------------------------------------------+
void CheckClosedOperations()
{
   // Verificar si la operación de banda media se cerró
   if(ticket_middle != 0)
   {
      bool middle_closed = true;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionSelectByTicket(PositionGetTicket(i)))
         {
            if(PositionGetInteger(POSITION_TICKET) == ticket_middle)
            {
               middle_closed = false;
               break;
            }
         }
      }
      
      if(middle_closed)
      {
         Print("Operación Banda Media cerrada - Ticket: ", ticket_middle);
         ticket_middle = 0;
         
         // Poner BE en la operación extrema
         if(ticket_extreme != 0)
         {
            SetBreakeven(ticket_extreme);
         }
      }
   }
   
   // Verificar si la operación extrema se cerró
   if(ticket_extreme != 0)
   {
      bool extreme_closed = true;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionSelectByTicket(PositionGetTicket(i)))
         {
            if(PositionGetInteger(POSITION_TICKET) == ticket_extreme)
            {
               extreme_closed = false;
               break;
            }
         }
      }
      
      if(extreme_closed)
      {
         Print("Operación Banda Extrema cerrada - Ticket: ", ticket_extreme);
         ticket_extreme = 0;
         
         // Poner BE en la operación de banda media
         if(ticket_middle != 0)
         {
            SetBreakeven(ticket_middle);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Poner Stop Loss en Breakeven                                      |
//+------------------------------------------------------------------+
void SetBreakeven(ulong ticket)
{
   if(!PositionSelectByTicket(ticket))
      return;
   
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL = PositionGetDouble(POSITION_SL);
   double currentTP = PositionGetDouble(POSITION_TP);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   // Verificar si ya está en BE
   if(currentSL == openPrice)
      return;
   
   bool result;
   
   if(posType == POSITION_TYPE_BUY)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      if(bid > openPrice)
      {
         result = trade.PositionModify(ticket, openPrice, currentTP);
         if(result)
            Print("BE aplicado en orden BUY - Ticket: ", ticket);
         else
            Print("Error al aplicar BE en BUY: ", GetLastError(), " - ", trade.ResultRetcode());
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(ask < openPrice)
      {
         result = trade.PositionModify(ticket, openPrice, currentTP);
         if(result)
            Print("BE aplicado en orden SELL - Ticket: ", ticket);
         else
            Print("Error al aplicar BE en SELL: ", GetLastError(), " - ", trade.ResultRetcode());
      }
   }
}
//+------------------------------------------------------------------+
