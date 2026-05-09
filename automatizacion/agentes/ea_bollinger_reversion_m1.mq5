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
input ENUM_TIMEFRAMES TimeFrame = PERIOD_M1;  // Timeframe del EA (M1, M5, M15, etc.)
input int    BB_Period = 40;           // Período Bandas Bollinger
input double BB_Deviation = 4.0;       // Desviación Bandas Bollinger
input int    ATR_Period = 7;           // Período ATR
input int    EMA_Period = 50;          // Período EMA (filtro tendencia)
input int    RSI_Period = 14;          // Período RSI (filtro momentum)
input int    RSI_Overbought = 70;      // Nivel sobrecompra RSI
input int    RSI_Oversold = 30;        // Nivel sobrevenda RSI
input double BB_Expansion_Max = 1.5;   // Máximo de expansión permitida (multiplicador del ancho promedio)
input double Candle_Max_Size_ATR = 2.0; // Tamaño máximo de vela para entrar (multiplicador del ATR) - filtro de fuerza
input double Trend_Angle_Min = 45.0;    // Ángulo mínimo para detectar tendencia (grados) - 0 = solo reversión
input bool   UseTrendMode = true;       // Usar modo tendencia cuando bandas inclinadas
input double RiskPercent = 1.0;         // Porcentaje de riesgo por operación (1% del capital)
input double LotSize = 0.01;           // Tamaño del lote (sobrescrito si RiskPercent > 0)
input int    MagicNumber = 654321;     // Número mágico (diferente al EA trend)
input int    Slippage = 3;              // Deslizamiento máximo
input double StopLoss_ATR_Mult = 5.0;  // Multiplicador ATR para Stop Loss - aumentado de 3.0 a 5.0
input double TakeProfit_ATR_Mult = 20.0; // Multiplicador ATR para Take Profit (operación con trailing) - aumentado de 15.0 a 20.0
input double TakeProfit_Quick_ATR = 5.0; // Multiplicador ATR para Take Profit rápido (ratio 1:2) - aumentado de 3.0 a 5.0
input bool   UseTrailingStop = true;   // Usar trailing stop
input double Trailing_Start_ATR = 3.0; // Distancia desde entrada para activar trailing (en ATR) - aumentado de 2.5 a 3.0
input double Trailing_Step_ATR = 2.0;  // Paso del trailing stop (en ATR) - aumentado de 1.5 a 2.0

//--- Variables globales
CTrade trade;
int BB_Handle;
int ATR_Handle;
int EMA_Handle;
int RSI_Handle;
double BB_Buffer[];
double ATR_Buffer[];
double EMA_Buffer[];
double RSI_Buffer[];
double BB_Upper, BB_Lower, BB_Middle;
double ATR_Value;
double EMA_Value;
double RSI_Value;
double BB_Width_Current;
double BB_Width_Average;
double BB_Slope; // Pendiente de la banda media
ulong ticket_quick = 0;     // Ticket para operación rápida (ratio 1:2)
ulong ticket_trailing = 0;  // Ticket para operación con trailing
bool reentry_after_win = false; // Flag para reentrada después de ganancia

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Inicializar indicadores
   BB_Handle = iBands(_Symbol, TimeFrame, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   ATR_Handle = iATR(_Symbol, TimeFrame, ATR_Period);
   EMA_Handle = iMA(_Symbol, TimeFrame, EMA_Period, 0, MODE_EMA, PRICE_CLOSE);
   RSI_Handle = iRSI(_Symbol, TimeFrame, RSI_Period, PRICE_CLOSE);
   
   if(BB_Handle == INVALID_HANDLE || ATR_Handle == INVALID_HANDLE || EMA_Handle == INVALID_HANDLE || RSI_Handle == INVALID_HANDLE)
   {
      Print("Error al crear indicadores");
      return(INIT_FAILED);
   }
   
   // Configurar buffers
   ArraySetAsSeries(BB_Buffer, true);
   ArraySetAsSeries(ATR_Buffer, true);
   ArraySetAsSeries(EMA_Buffer, true);
   ArraySetAsSeries(RSI_Buffer, true);
   
   // Configurar trade
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   
   Print("EA Bollinger Reversión iniciado");
   Print("Timeframe: ", EnumToString(TimeFrame));
   Print("BB: ", BB_Period, " períodos, desviación: ", BB_Deviation);
   Print("ATR: ", ATR_Period, " períodos");
   Print("EMA: ", EMA_Period, " períodos (filtro tendencia)");
   Print("RSI: ", RSI_Period, " períodos (filtro momentum)");
   Print("Filtro expansión BB máximo: ", BB_Expansion_Max, "x ancho promedio");
   Print("Filtro fuerza vela máximo: ", Candle_Max_Size_ATR, "x ATR");
   Print("Modo tendencia: ", UseTrendMode, " - Ángulo mínimo: ", Trend_Angle_Min, " grados");
   Print("Riesgo por operación: ", RiskPercent, "% del capital");
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
   if(EMA_Handle != INVALID_HANDLE)
      IndicatorRelease(EMA_Handle);
   if(RSI_Handle != INVALID_HANDLE)
      IndicatorRelease(RSI_Handle);
   
   Print("EA Bollinger Reversión detenido");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Verificar si estamos en una nueva barra
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, TimeFrame, 0);
   
   if(currentBarTime == lastBarTime)
      return;
   
   lastBarTime = currentBarTime;
   
   // Calcular indicadores
   CalculateIndicators();
   
   // Verificar operaciones existentes
   CheckOperations();
   
   // Si hay flag de reentrada después de ganancia, abrir nueva operación
   if(reentry_after_win && ticket_quick == 0 && ticket_trailing == 0)
   {
      Print("Reentrada después de ganancia fuera de banda");
      reentry_after_win = false;
      CheckReversionSignals();
      return;
   }
   
   // Si no hay operaciones abiertas, buscar señales de reversión
   if(ticket_quick == 0 && ticket_trailing == 0)
   {
      CheckReversionSignals();
   }
   else
   {
      // Si hay operaciones abiertas, gestionarlas
      if(ticket_quick != 0)
      {
         CheckQuickExit(); // Verificar si operación rápida alcanzó TP 1:2
      }
      if(ticket_trailing != 0 && UseTrailingStop)
      {
         ManageTrailingStop(); // Aplicar trailing a operación con trailing
      }
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
   
   // Calcular ancho actual de las bandas
   BB_Width_Current = BB_Upper - BB_Lower;
   
   // Calcular ancho promedio de las últimas BB_Period barras
   double totalWidth = 0;
   for(int i = 1; i <= BB_Period; i++)
   {
      totalWidth += (bb_upper[i] - bb_lower[i]);
   }
   BB_Width_Average = totalWidth / BB_Period;
   
   // Copiar datos de ATR
   if(CopyBuffer(ATR_Handle, 0, 0, 3, ATR_Buffer) < 3)
      return;
   
   ATR_Value = ATR_Buffer[1];
   
   // Copiar datos de EMA
   if(CopyBuffer(EMA_Handle, 0, 0, 3, EMA_Buffer) < 3)
      return;
   
   EMA_Value = EMA_Buffer[1];
   
   // Copiar datos de RSI
   if(CopyBuffer(RSI_Handle, 0, 0, 3, RSI_Buffer) < 3)
      return;
   
   RSI_Value = RSI_Buffer[1];
}

//+------------------------------------------------------------------+
//| Calcular tamaño de lote basado en riesgo porcentual               |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_distance)
{
   if(RiskPercent <= 0)
      return LotSize;
   
   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = accountBalance * (RiskPercent / 100.0);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   
   // Calcular puntos en el instrumento
   double points = sl_distance / tickSize;
   
   // Calcular lote basado en riesgo
   double lotSize = riskAmount / (points * tickValue);
   
   // Ajustar a lote mínimo y máximo del instrumento
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   lotSize = MathMax(lotSize, minLot);
   lotSize = MathMin(lotSize, maxLot);
   
   return lotSize;
}

//+------------------------------------------------------------------+
//| Calcular ángulo de la pendiente en grados                         |
//+------------------------------------------------------------------+
double CalculateSlopeAngle(double slope)
{
   // Convertir pendiente a ángulo en grados
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
//| Verificar señales de reversión                                     |
//+------------------------------------------------------------------+
void CheckReversionSignals()
{
   double close = iClose(_Symbol, TimeFrame, 1);
   double high = iHigh(_Symbol, TimeFrame, 1);
   double low = iLow(_Symbol, TimeFrame, 1);
   
   // Calcular tamaño de lote basado en riesgo
   double sl_distance = ATR_Value * StopLoss_ATR_Mult;
   double calculated_lot = CalculateLotSize(sl_distance);
   
   // Verificar si hay tendencia
   bool trending = IsTrending();
   int trend_direction = GetTrendDirection();
   
   // FILTROS COMUNES
   bool bb_expansion_filter = (BB_Width_Current <= (BB_Width_Average * BB_Expansion_Max));
   bool ema_filter_buy = (close < EMA_Value); // Precio por debajo de EMA (no tendencia alcista)
   bool ema_filter_sell = (close > EMA_Value); // Precio por encima de EMA (no tendencia bajista)
   bool rsi_filter_buy = (RSI_Value < RSI_Overbought); // RSI no en sobrecompra
   bool rsi_filter_sell = (RSI_Value > RSI_Oversold); // RSI no en sobrevenda
   
   // Calcular tamaño de la vela
   double candle_size = high - low;
   bool candle_force_filter = (candle_size <= (ATR_Value * Candle_Max_Size_ATR)); // Vela no muy grande
   
   // MODO TENDENCIA: Bandas inclinadas
   if(UseTrendMode && trending)
   {
      // Señal de tendencia alcista: precio toca banda media y tendencia es alcista
      if(trend_direction == 1 && close <= BB_Middle && close >= BB_Lower)
      {
         if(bb_expansion_filter && candle_force_filter)
         {
            // Operación 1: Rápida (ratio 1:2)
            double sl1 = close - (ATR_Value * StopLoss_ATR_Mult);
            double tp1 = close + (ATR_Value * TakeProfit_Quick_ATR);
            ticket_quick = OpenOrder(ORDER_TYPE_BUY, calculated_lot, sl1, tp1, "BB Trend Quick Buy");
            Print("Tendencia BUY Rápida: TP 1:2 - Ángulo: ", CalculateSlopeAngle(BB_Slope), " Vela: ", candle_size, " - Ticket: ", ticket_quick);
            
            // Operación 2: Con trailing stop
            if(ticket_quick != 0)
            {
               double sl2 = close - (ATR_Value * StopLoss_ATR_Mult);
               double tp2 = close + (ATR_Value * TakeProfit_ATR_Mult);
               ticket_trailing = OpenOrder(ORDER_TYPE_BUY, calculated_lot, sl2, tp2, "BB Trend Trailing Buy");
               Print("Tendencia BUY Trailing: TP largo - Ticket: ", ticket_trailing);
            }
         }
      }
      // Señal de tendencia bajista: precio toca banda media y tendencia es bajista
      else if(trend_direction == -1 && close >= BB_Middle && close <= BB_Upper)
      {
         if(bb_expansion_filter && candle_force_filter)
         {
            // Operación 1: Rápida (ratio 1:2)
            double sl1 = close + (ATR_Value * StopLoss_ATR_Mult);
            double tp1 = close - (ATR_Value * TakeProfit_Quick_ATR);
            ticket_quick = OpenOrder(ORDER_TYPE_SELL, calculated_lot, sl1, tp1, "BB Trend Quick Sell");
            Print("Tendencia SELL Rápida: TP 1:2 - Ángulo: ", CalculateSlopeAngle(BB_Slope), " Vela: ", candle_size, " - Ticket: ", ticket_quick);
            
            // Operación 2: Con trailing stop
            if(ticket_quick != 0)
            {
               double sl2 = close + (ATR_Value * StopLoss_ATR_Mult);
               double tp2 = close - (ATR_Value * TakeProfit_ATR_Mult);
               ticket_trailing = OpenOrder(ORDER_TYPE_SELL, calculated_lot, sl2, tp2, "BB Trend Trailing Sell");
               Print("Tendencia SELL Trailing: TP largo - Ticket: ", ticket_trailing);
            }
         }
      }
   }
   // MODO REVERSIÓN: Bandas planas
   else
   {
      // Señal de reversión alcista: precio toca banda inferior
      if(low <= BB_Lower)
      {
         if(bb_expansion_filter && ema_filter_buy && rsi_filter_buy && candle_force_filter)
         {
            // Operación 1: Rápida (ratio 1:2)
            double sl1 = close - (ATR_Value * StopLoss_ATR_Mult);
            double tp1 = close + (ATR_Value * TakeProfit_Quick_ATR);
            ticket_quick = OpenOrder(ORDER_TYPE_BUY, calculated_lot, sl1, tp1, "BB Reversion Quick Buy");
            Print("Reversión BUY Rápida: TP 1:2 - EMA: ", EMA_Value, " RSI: ", RSI_Value, " Vela: ", candle_size, " Ancho BB: ", BB_Width_Current, " - Ticket: ", ticket_quick);
            
            // Operación 2: Con trailing stop
            if(ticket_quick != 0)
            {
               double sl2 = close - (ATR_Value * StopLoss_ATR_Mult);
               double tp2 = close + (ATR_Value * TakeProfit_ATR_Mult);
               ticket_trailing = OpenOrder(ORDER_TYPE_BUY, calculated_lot, sl2, tp2, "BB Reversion Trailing Buy");
               Print("Reversión BUY Trailing: TP largo - Ticket: ", ticket_trailing);
            }
         }
         else
         {
            Print("BUY filtrado - EMA: ", close, " vs ", EMA_Value, " - RSI: ", RSI_Value, " (max ", RSI_Overbought, ") - Vela: ", candle_size, " (máximo: ", ATR_Value * Candle_Max_Size_ATR, ") - BB: ", BB_Width_Current, " (máximo: ", BB_Width_Average * BB_Expansion_Max, ")");
         }
      }
      // Señal de reversión bajista: precio toca banda superior
      else if(high >= BB_Upper)
      {
         if(bb_expansion_filter && ema_filter_sell && rsi_filter_sell && candle_force_filter)
         {
            // Operación 1: Rápida (ratio 1:2)
            double sl1 = close + (ATR_Value * StopLoss_ATR_Mult);
            double tp1 = close - (ATR_Value * TakeProfit_Quick_ATR);
            ticket_quick = OpenOrder(ORDER_TYPE_SELL, calculated_lot, sl1, tp1, "BB Reversion Quick Sell");
            Print("Reversión SELL Rápida: TP 1:2 - EMA: ", EMA_Value, " RSI: ", RSI_Value, " Vela: ", candle_size, " Ancho BB: ", BB_Width_Current, " - Ticket: ", ticket_quick);
            
            // Operación 2: Con trailing stop
            if(ticket_quick != 0)
            {
               double sl2 = close + (ATR_Value * StopLoss_ATR_Mult);
               double tp2 = close - (ATR_Value * TakeProfit_ATR_Mult);
               ticket_trailing = OpenOrder(ORDER_TYPE_SELL, calculated_lot, sl2, tp2, "BB Reversion Trailing Sell");
               Print("Reversión SELL Trailing: TP largo - Ticket: ", ticket_trailing);
            }
         }
         else
         {
            Print("SELL filtrado - EMA: ", close, " vs ", EMA_Value, " - RSI: ", RSI_Value, " (min ", RSI_Oversold, ") - Vela: ", candle_size, " (máximo: ", ATR_Value * Candle_Max_Size_ATR, ") - BB: ", BB_Width_Current, " (máximo: ", BB_Width_Average * BB_Expansion_Max, ")");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Verificar salida rápida (ratio 1:2)                                 |
//+------------------------------------------------------------------+
void CheckQuickExit()
{
   if(!PositionSelectByTicket(ticket_quick))
   {
      ticket_quick = 0;
      return;
   }
   
   double close = iClose(_Symbol, TimeFrame, 0);
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double tp = PositionGetDouble(POSITION_TP);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   // Verificar si alcanzó el TP (ratio 1:2)
   if(posType == POSITION_TYPE_BUY)
   {
      if(close >= tp)
      {
         // Verificar si cerró fuera de la banda (ganadora)
         double currentBB_Upper = BB_Upper;
         double currentBB_Lower = BB_Lower;
         bool closed_outside_band = (close > currentBB_Upper || close < currentBB_Lower);
         
         ClosePosition(ticket_quick);
         Print("Operación BUY Rápida cerrada por TP 1:2 - Ticket: ", ticket_quick, " - Fuera de banda: ", closed_outside_band);
         ticket_quick = 0;
         
         // Activar reentrada si cerró ganadora fuera de banda
         if(closed_outside_band)
            reentry_after_win = true;
         
         // Mover SL de operación trailing a break even
         if(ticket_trailing != 0 && PositionSelectByTicket(ticket_trailing))
         {
            double openPriceTrailing = PositionGetDouble(POSITION_PRICE_OPEN);
            double currentSL = PositionGetDouble(POSITION_SL);
            
            if(currentSL < openPriceTrailing)
            {
               if(trade.PositionModify(ticket_trailing, openPriceTrailing, PositionGetDouble(POSITION_TP)))
                  Print("Break even aplicado a BUY Trailing - Ticket: ", ticket_trailing);
            }
         }
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      if(close <= tp)
      {
         // Verificar si cerró fuera de la banda (ganadora)
         double currentBB_Upper = BB_Upper;
         double currentBB_Lower = BB_Lower;
         bool closed_outside_band = (close > currentBB_Upper || close < currentBB_Lower);
         
         ClosePosition(ticket_quick);
         Print("Operación SELL Rápida cerrada por TP 1:2 - Ticket: ", ticket_quick, " - Fuera de banda: ", closed_outside_band);
         ticket_quick = 0;
         
         // Activar reentrada si cerró ganadora fuera de banda
         if(closed_outside_band)
            reentry_after_win = true;
         
         // Mover SL de operación trailing a break even
         if(ticket_trailing != 0 && PositionSelectByTicket(ticket_trailing))
         {
            double openPriceTrailing = PositionGetDouble(POSITION_PRICE_OPEN);
            double currentSL = PositionGetDouble(POSITION_SL);
            
            if(currentSL > openPriceTrailing || currentSL == 0)
            {
               if(trade.PositionModify(ticket_trailing, openPriceTrailing, PositionGetDouble(POSITION_TP)))
                  Print("Break even aplicado a SELL Trailing - Ticket: ", ticket_trailing);
            }
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
   bool quick_exists = false;
   bool trailing_exists = false;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            string comment = PositionGetString(POSITION_COMMENT);
            if(StringFind(comment, "Quick") != -1 || StringFind(comment, "Trend") != -1)
            {
               ticket_quick = PositionGetInteger(POSITION_TICKET);
               quick_exists = true;
            }
            else if(StringFind(comment, "Trailing") != -1)
            {
               ticket_trailing = PositionGetInteger(POSITION_TICKET);
               trailing_exists = true;
            }
         }
      }
   }
   
   if(!quick_exists)
      ticket_quick = 0;
   
   if(!trailing_exists)
      ticket_trailing = 0;
}

//+------------------------------------------------------------------+
//| Gestionar Trailing Stop                                            |
//+------------------------------------------------------------------+
void ManageTrailingStop()
{
   if(!PositionSelectByTicket(ticket_trailing))
      return;
   
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL = PositionGetDouble(POSITION_SL);
   double currentTP = PositionGetDouble(POSITION_TP);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   double currentPrice;
   if(posType == POSITION_TYPE_BUY)
      currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   else
      currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   double profit = 0;
   if(posType == POSITION_TYPE_BUY)
      profit = currentPrice - openPrice;
   else
      profit = openPrice - currentPrice;
   
   // Calcular distancia de activación en puntos
   double activationDistance = ATR_Value * Trailing_Start_ATR;
   double trailingStep = ATR_Value * Trailing_Step_ATR;
   
   // Verificar si se activó el trailing
   if(profit >= activationDistance)
   {
      double newSL, newTP;
      
      if(posType == POSITION_TYPE_BUY)
      {
         // Para BUY: SL sigue el precio hacia arriba
         newSL = currentPrice - trailingStep;
         
         // Solo modificar si el nuevo SL es mayor que el actual
         if(newSL > currentSL || currentSL == 0)
         {
            // TP también persigue el precio
            newTP = currentPrice + (TakeProfit_ATR_Mult * ATR_Value);
            
            if(trade.PositionModify(ticket_trailing, newSL, newTP))
            {
               Print("Trailing BUY: SL actualizado a ", newSL, " - TP actualizado a ", newTP);
            }
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         // Para SELL: SL sigue el precio hacia abajo
         newSL = currentPrice + trailingStep;
         
         // Solo modificar si el nuevo SL es menor que el actual
         if(newSL < currentSL || currentSL == 0)
         {
            // TP también persigue el precio
            newTP = currentPrice - (TakeProfit_ATR_Mult * ATR_Value);
            
            if(trade.PositionModify(ticket_trailing, newSL, newTP))
            {
               Print("Trailing SELL: SL actualizado a ", newSL, " - TP actualizado a ", newTP);
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
