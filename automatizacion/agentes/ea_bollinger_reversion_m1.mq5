//+------------------------------------------------------------------+
//| EA_Bollinger_Reversion_M1.mq5                                     |
//| QuantumHive Algorithmic Trading                                  |
//| EA M1 con Bollinger (40, 4.0) y ATR (7) - Reversión              |
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
input int    MagicNumber = 654321;     // Número mágico (diferente al EA trend)
input int    Slippage = 3;              // Deslizamiento máximo
input double StopLoss_ATR_Mult = 2.0;  // Multiplicador ATR para Stop Loss
input double TakeProfit_ATR_Mult = 1.5; // Multiplicador ATR para Take Profit (más corto)

//--- Variables globales
CTrade trade;
int BB_Handle;
int ATR_Handle;
double BB_Buffer[];
double ATR_Buffer[];
double BB_Upper, BB_Lower, BB_Middle;
double ATR_Value;
ulong current_ticket = 0;

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
   
   Print("EA Bollinger Reversión M1 iniciado");
   Print("BB: ", BB_Period, " períodos, desviación: ", BB_Deviation);
   Print("ATR: ", ATR_Period, " períodos");
   Print("MagicNumber: ", MagicNumber);
   
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
   
   Print("EA Bollinger Reversión M1 detenido");
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
   
   // Si no hay operación abierta, buscar señales de reversión
   if(current_ticket == 0)
   {
      CheckReversionSignals();
   }
   else
   {
      // Si hay operación abierta, verificar salida en banda media
      CheckExitSignal();
   }
}

//+------------------------------------------------------------------+
//| Calcular indicadores                                               |
//+------------------------------------------------------------------+
void CalculateIndicators()
{
   // Copiar datos de Bollinger
   double bb_upper[], bb_lower[], bb_middle[];
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_lower, true);
   ArraySetAsSeries(bb_middle, true);
   
   if(CopyBuffer(BB_Handle, 0, 0, 3, bb_middle) < 3)
      return;
   if(CopyBuffer(BB_Handle, 1, 0, 3, bb_upper) < 3)
      return;
   if(CopyBuffer(BB_Handle, 2, 0, 3, bb_lower) < 3)
      return;
   
   BB_Middle = bb_middle[1];
   BB_Upper = bb_upper[1];
   BB_Lower = bb_lower[1];
   
   // Copiar datos de ATR
   if(CopyBuffer(ATR_Handle, 0, 0, 3, ATR_Buffer) < 3)
      return;
   
   ATR_Value = ATR_Buffer[1];
}

//+------------------------------------------------------------------+
//| Verificar señales de reversión                                     |
//+------------------------------------------------------------------+
void CheckReversionSignals()
{
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double high = iHigh(_Symbol, PERIOD_M1, 1);
   double low = iLow(_Symbol, PERIOD_M1, 1);
   
   // Señal de reversión alcista: precio toca banda inferior
   if(low <= BB_Lower)
   {
      double sl = close - (ATR_Value * StopLoss_ATR_Mult);
      double tp = BB_Middle; // Salida en banda media
      current_ticket = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp, "BB Reversion Buy");
      Print("Reversión BUY: Precio tocó banda inferior - Ticket: ", current_ticket);
   }
   // Señal de reversión bajista: precio toca banda superior
   else if(high >= BB_Upper)
   {
      double sl = close + (ATR_Value * StopLoss_ATR_Mult);
      double tp = BB_Middle; // Salida en banda media
      current_ticket = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp, "BB Reversion Sell");
      Print("Reversión SELL: Precio tocó banda superior - Ticket: ", current_ticket);
   }
}

//+------------------------------------------------------------------+
//| Verificar señal de salida (banda media)                            |
//+------------------------------------------------------------------+
void CheckExitSignal()
{
   if(!PositionSelectByTicket(current_ticket))
   {
      current_ticket = 0;
      return;
   }
   
   double close = iClose(_Symbol, PERIOD_M1, 0);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   if(posType == POSITION_TYPE_BUY)
   {
      // Salir cuando el precio cruza la banda media hacia abajo
      if(close <= BB_Middle)
      {
         ClosePosition(current_ticket);
         Print("Salida BUY: Precio cruzó banda media - Ticket: ", current_ticket);
         current_ticket = 0;
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      // Salir cuando el precio cruza la banda media hacia arriba
      if(close >= BB_Middle)
      {
         ClosePosition(current_ticket);
         Print("Salida SELL: Precio cruzó banda media - Ticket: ", current_ticket);
         current_ticket = 0;
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
//| Cerrar posición                                                   |
//+------------------------------------------------------------------+
bool ClosePosition(ulong ticket)
{
   if(!trade.PositionClose(ticket))
   {
      Print("Error al cerrar posición: ", GetLastError(), " - ", trade.ResultRetcode(), " - ", trade.ResultRetcodeDescription());
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Verificar operaciones existentes                                   |
//+------------------------------------------------------------------+
void CheckOperations()
{
   bool position_exists = false;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            string comment = PositionGetString(POSITION_COMMENT);
            if(StringFind(comment, "BB Reversion") != -1)
            {
               current_ticket = PositionGetInteger(POSITION_TICKET);
               position_exists = true;
               break;
            }
         }
      }
   }
   
   if(!position_exists)
      current_ticket = 0;
}
//+------------------------------------------------------------------+
