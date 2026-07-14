//+------------------------------------------------------------------+
//| EA_Bollinger_Doble_Entrada_M1.mq5                                 |
//| QuantumHive Algorithmic Trading                                  |
//| EA M1 con Bollinger (40, 4.0) - Doble Entrada                     |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//--- Parámetros de entrada
input int    BB_Period = 40;           // Período Bandas Bollinger
input double BB_Deviation = 4.0;       // Desviación Bandas Bollinger
input double Trend_Angle_Min = 45.0;    // Ángulo mínimo para detectar tendencia (grados)
input bool   UseTrendMode = true;       // Usar modo tendencia cuando bandas inclinadas
input double LotSize = 0.01;           // Tamaño del lote
input int    MagicNumber = 654322;     // Número mágico
input int    Slippage = 3;              // Deslizamiento máximo

// Filtro horario (Argentina - UTC-3)
input int    StartHour = 10;           // Hora inicio (Argentina)
input int    StartMinute = 0;          // Minuto inicio
input int    EndHour = 13;             // Hora fin (Argentina)
input int    EndMinute = 0;            // Minuto fin

//--- Variables globales
CTrade trade;
int BB_Handle;
double BB_Buffer[];
double BB_Upper, BB_Lower, BB_Middle;
double BB_Slope; // Pendiente de la banda media
ulong ticket_middle = 0;      // Ticket para operación que cierra en banda media
ulong ticket_opposite = 0;    // Ticket para operación que cierra en banda contraria

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Inicializar indicador Bollinger
   BB_Handle = iBands(_Symbol, PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   
   if(BB_Handle == INVALID_HANDLE)
   {
      Print("Error al crear indicador Bollinger");
      return(INIT_FAILED);
   }
   
   // Configurar buffer
   ArraySetAsSeries(BB_Buffer, true);
   
   // Configurar trade
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   
   Print("EA Bollinger Doble Entrada iniciado");
   Print("BB: ", BB_Period, " períodos, desviación: ", BB_Deviation);
   Print("Modo tendencia: ", UseTrendMode, " - Ángulo mínimo: ", Trend_Angle_Min, " grados");
   Print("Filtro horario: ", StartHour, ":", StartMinute, " - ", EndHour, ":", EndMinute, " (Argentina)");
   Print("MagicNumber: ", MagicNumber);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Liberar handle
   if(BB_Handle != INVALID_HANDLE)
      IndicatorRelease(BB_Handle);
   
   Print("EA Bollinger Doble Entrada detenido");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Verificar filtro horario
   if(!IsTradingTime())
      return;
   
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
   
   // Si no hay operaciones abiertas, buscar señales
   if(ticket_middle == 0 && ticket_opposite == 0)
   {
      CheckSignals();
   }
   else
   {
      // Si hay operaciones abiertas, gestionar salidas
      ManageExits();
   }
}

//+------------------------------------------------------------------+
//| Verificar si es horario de trading (Argentina UTC-3)               |
//+------------------------------------------------------------------+
bool IsTradingTime()
{
   datetime currentTime = TimeCurrent();
   MqlDateTime timeStruct;
   TimeToStruct(currentTime, timeStruct);
   
   // Convertir a hora Argentina (UTC-3)
   int argentinaHour = timeStruct.hour + 3;
   if(argentinaHour >= 24)
      argentinaHour -= 24;
   
   // Verificar si está en el rango permitido
   int currentMinutes = argentinaHour * 60 + timeStruct.min;
   int startMinutes = StartHour * 60 + StartMinute;
   int endMinutes = EndHour * 60 + EndMinute;
   
   return (currentMinutes >= startMinutes && currentMinutes < endMinutes);
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
   
   if(CopyBuffer(BB_Handle, 0, 0, BB_Period + 1, bb_middle) < BB_Period + 1)
      return;
   if(CopyBuffer(BB_Handle, 1, 0, BB_Period + 1, bb_upper) < BB_Period + 1)
      return;
   if(CopyBuffer(BB_Handle, 2, 0, BB_Period + 1, bb_lower) < BB_Period + 1)
      return;
   
   BB_Middle = bb_middle[1];
   BB_Upper = bb_upper[1];
   BB_Lower = bb_lower[1];
   
   // Calcular pendiente de la banda media (ángulo de tendencia)
   double bb_middle_prev = bb_middle[BB_Period];
   BB_Slope = (BB_Middle - bb_middle_prev) / BB_Period;
}

//+------------------------------------------------------------------+
//| Calcular ángulo de la pendiente en grados                         |
//+------------------------------------------------------------------+
double CalculateSlopeAngle(double slope)
{
   double angle = MathArctan(slope) * 180.0 / M_PI;
   return MathAbs(angle);
}

//+------------------------------------------------------------------+
//| Verificar si hay tendencia (bandas inclinadas)                     |
//+------------------------------------------------------------------+
bool IsTrending()
{
   double angle = CalculateSlopeAngle(BB_Slope);
   return (angle >= Trend_Angle_Min);
}

//+------------------------------------------------------------------+
//| Verificar dirección de la tendencia                                |
//+------------------------------------------------------------------+
int GetTrendDirection()
{
   if(BB_Slope > 0)
      return 1; // Tendencia alcista
   else if(BB_Slope < 0)
      return -1; // Tendencia bajista
   else
      return 0; // Sin tendencia
}

//+------------------------------------------------------------------+
//| Verificar si la vela tiene mecha y cuerpo dentro de las bandas    |
//+------------------------------------------------------------------+
bool IsCandleInsideBands()
{
   double open = iOpen(_Symbol, PERIOD_M1, 1);
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double high = iHigh(_Symbol, PERIOD_M1, 1);
   double low = iLow(_Symbol, PERIOD_M1, 1);
   
   // Verificar si mecha y cuerpo están dentro de las bandas
   bool bodyInside = (open >= BB_Lower && open <= BB_Upper && close >= BB_Lower && close <= BB_Upper);
   bool wickInside = (high <= BB_Upper && low >= BB_Lower);
   
   return bodyInside && wickInside;
}

//+------------------------------------------------------------------+
//| Verificar señales                                                 |
//+------------------------------------------------------------------+
void CheckSignals()
{
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double high = iHigh(_Symbol, PERIOD_M1, 1);
   double low = iLow(_Symbol, PERIOD_M1, 1);
   
   // Verificar si hay tendencia
   bool trending = IsTrending();
   int trend_direction = GetTrendDirection();
   
   // MODO B (TENDENCIA): Bandas inclinadas a 45°
   if(UseTrendMode && trending)
   {
      // Señal de tendencia alcista: precio toca banda media y tendencia es alcista
      if(trend_direction == 1 && close <= BB_Middle && close >= BB_Lower)
      {
         // Entrada a favor de la tendencia
         double sl = low;
         double tp_middle = BB_Middle;
         double tp_opposite = BB_Upper;
         
         ticket_middle = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp_middle, "BB Trend Middle Buy");
         Print("Tendencia BUY - TP banda media - Ticket: ", ticket_middle);
         
         if(ticket_middle != 0)
         {
            ticket_opposite = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp_opposite, "BB Trend Opposite Buy");
            Print("Tendencia BUY - TP banda contraria - Ticket: ", ticket_opposite);
         }
      }
      // Señal de tendencia bajista: precio toca banda media y tendencia es bajista
      else if(trend_direction == -1 && close >= BB_Middle && close <= BB_Upper)
      {
         // Entrada a favor de la tendencia
         double sl = high;
         double tp_middle = BB_Middle;
         double tp_opposite = BB_Lower;
         
         ticket_middle = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp_middle, "BB Trend Middle Sell");
         Print("Tendencia SELL - TP banda media - Ticket: ", ticket_middle);
         
         if(ticket_middle != 0)
         {
            ticket_opposite = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp_opposite, "BB Trend Opposite Sell");
            Print("Tendencia SELL - TP banda contraria - Ticket: ", ticket_opposite);
         }
      }
   }
   // MODO A (REVERSIÓN): Bandas planas
   else
   {
      // Verificar si la vela tiene mecha y cuerpo dentro de las bandas
      if(!IsCandleInsideBands())
         return;
      
      // Señal de reversión alcista: precio toca banda inferior
      if(low <= BB_Lower)
      {
         double sl = low;
         double tp_middle = BB_Middle;
         double tp_opposite = BB_Upper;
         
         ticket_middle = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp_middle, "BB Reversion Middle Buy");
         Print("Reversión BUY - TP banda media - Ticket: ", ticket_middle);
         
         if(ticket_middle != 0)
         {
            ticket_opposite = OpenOrder(ORDER_TYPE_BUY, LotSize, sl, tp_opposite, "BB Reversion Opposite Buy");
            Print("Reversión BUY - TP banda contraria - Ticket: ", ticket_opposite);
         }
      }
      // Señal de reversión bajista: precio toca banda superior
      else if(high >= BB_Upper)
      {
         double sl = high;
         double tp_middle = BB_Middle;
         double tp_opposite = BB_Lower;
         
         ticket_middle = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp_middle, "BB Reversion Middle Sell");
         Print("Reversión SELL - TP banda media - Ticket: ", ticket_middle);
         
         if(ticket_middle != 0)
         {
            ticket_opposite = OpenOrder(ORDER_TYPE_SELL, LotSize, sl, tp_opposite, "BB Reversion Opposite Sell");
            Print("Reversión SELL - TP banda contraria - Ticket: ", ticket_opposite);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Gestionar salidas                                                 |
//+------------------------------------------------------------------+
void ManageExits()
{
   double close = iClose(_Symbol, PERIOD_M1, 0);
   
   // Verificar salida de operación que cierra en banda media
   if(ticket_middle != 0)
   {
      if(PositionSelectByTicket(ticket_middle))
      {
         double tp = PositionGetDouble(POSITION_TP);
         ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         
         if(posType == POSITION_TYPE_BUY && close >= tp)
         {
            ClosePosition(ticket_middle);
            Print("Operación BUY Middle cerrada - Ticket: ", ticket_middle);
            ticket_middle = 0;
         }
         else if(posType == POSITION_TYPE_SELL && close <= tp)
         {
            ClosePosition(ticket_middle);
            Print("Operación SELL Middle cerrada - Ticket: ", ticket_middle);
            ticket_middle = 0;
         }
      }
      else
      {
         ticket_middle = 0;
      }
   }
   
   // Verificar salida de operación que cierra en banda contraria
   if(ticket_opposite != 0)
   {
      if(PositionSelectByTicket(ticket_opposite))
      {
         double tp = PositionGetDouble(POSITION_TP);
         ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         
         if(posType == POSITION_TYPE_BUY && close >= tp)
         {
            ClosePosition(ticket_opposite);
            Print("Operación BUY Opposite cerrada - Ticket: ", ticket_opposite);
            ticket_opposite = 0;
         }
         else if(posType == POSITION_TYPE_SELL && close <= tp)
         {
            ClosePosition(ticket_opposite);
            Print("Operación SELL Opposite cerrada - Ticket: ", ticket_opposite);
            ticket_opposite = 0;
         }
      }
      else
      {
         ticket_opposite = 0;
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
   bool middle_exists = false;
   bool opposite_exists = false;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            string comment = PositionGetString(POSITION_COMMENT);
            if(StringFind(comment, "Middle") != -1)
            {
               ticket_middle = PositionGetInteger(POSITION_TICKET);
               middle_exists = true;
            }
            else if(StringFind(comment, "Opposite") != -1)
            {
               ticket_opposite = PositionGetInteger(POSITION_TICKET);
               opposite_exists = true;
            }
         }
      }
   }
   
   if(!middle_exists)
      ticket_middle = 0;
   
   if(!opposite_exists)
      ticket_opposite = 0;
}
//+------------------------------------------------------------------+
