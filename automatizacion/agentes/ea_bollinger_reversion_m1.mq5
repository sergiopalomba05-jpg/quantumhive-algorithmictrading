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
input int    RSI_Period = 14;          // Período RSI (filtro momentum)
input int    EMA_Period = 50;          // Período EMA (filtro tendencia)
input int    ADX_Period = 14;          // Período ADX (fuerza de tendencia)
input int    ADX_Max = 40;             // Máximo ADX para operar reversión (tendencia débil) - aumentado de 30 a 40
input int    MACD_Fast = 12;           // Período rápido MACD
input int    MACD_Slow = 26;           // Período lento MACD
input int    MACD_Signal = 9;          // Período señal MACD
input int    RSI_Overbought = 80;      // Nivel sobrecompra RSI - aumentado de 75 a 80
input int    RSI_Oversold = 20;        // Nivel sobrevenda RSI - reducido de 25 a 20
input double LotSize = 0.01;           // Tamaño del lote
input int    MagicNumber = 654321;     // Número mágico (diferente al EA trend)
input int    Slippage = 3;              // Deslizamiento máximo
input double StopLoss_ATR_Mult = 4.0;  // Multiplicador ATR para Stop Loss
input double TakeProfit_ATR_Mult = 12.0; // Multiplicador ATR para Take Profit (operación con trailing) - aumentado de 8.0 a 12.0
input double TakeProfit_Quick_ATR = 2.0; // Multiplicador ATR para Take Profit rápido (ratio 1:2)
input bool   UseTrailingStop = true;   // Usar trailing stop
input double Trailing_Start_ATR = 2.5; // Distancia desde entrada para activar trailing (en ATR) - aumentado de 2.0 a 2.5
input double Trailing_Step_ATR = 1.5;  // Paso del trailing stop (en ATR) - aumentado de 1.0 a 1.5 (más amplio)

//--- Variables globales
CTrade trade;
int BB_Handle;
int ATR_Handle;
int RSI_Handle;
int EMA_Handle;
int ADX_Handle;
int MACD_Handle;
double BB_Buffer[];
double ATR_Buffer[];
double RSI_Buffer[];
double EMA_Buffer[];
double ADX_Buffer[];
double MACD_Main_Buffer[];
double MACD_Signal_Buffer[];
double BB_Upper, BB_Lower, BB_Middle;
double ATR_Value;
double RSI_Value;
double EMA_Value;
double ADX_Value;
double MACD_Main;
double MACD_Signal_Value;  // Valor actual del indicador MACD Signal (evita conflicto con parámetro)
ulong ticket_quick = 0;     // Ticket para operación rápida (ratio 1:2)
ulong ticket_trailing = 0;  // Ticket para operación con trailing

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Inicializar indicadores
   BB_Handle = iBands(_Symbol, PERIOD_M1, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   ATR_Handle = iATR(_Symbol, PERIOD_M1, ATR_Period);
   RSI_Handle = iRSI(_Symbol, PERIOD_M1, RSI_Period, PRICE_CLOSE);
   EMA_Handle = iMA(_Symbol, PERIOD_M1, EMA_Period, 0, MODE_EMA, PRICE_CLOSE);
   ADX_Handle = iADX(_Symbol, PERIOD_M1, ADX_Period);
   MACD_Handle = iMACD(_Symbol, PERIOD_M1, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);
   
   if(BB_Handle == INVALID_HANDLE || ATR_Handle == INVALID_HANDLE || RSI_Handle == INVALID_HANDLE || EMA_Handle == INVALID_HANDLE || ADX_Handle == INVALID_HANDLE || MACD_Handle == INVALID_HANDLE)
   {
      Print("Error al crear indicadores");
      return(INIT_FAILED);
   }
   
   // Configurar buffers
   ArraySetAsSeries(BB_Buffer, true);
   ArraySetAsSeries(ATR_Buffer, true);
   ArraySetAsSeries(RSI_Buffer, true);
   ArraySetAsSeries(EMA_Buffer, true);
   ArraySetAsSeries(ADX_Buffer, true);
   ArraySetAsSeries(MACD_Main_Buffer, true);
   ArraySetAsSeries(MACD_Signal_Buffer, true);
   
   // Configurar trade
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   
   Print("EA Bollinger Reversión M1 iniciado");
   Print("BB: ", BB_Period, " períodos, desviación: ", BB_Deviation);
   Print("ATR: ", ATR_Period, " períodos");
   Print("RSI: ", RSI_Period, " períodos (filtro momentum)");
   Print("EMA: ", EMA_Period, " períodos (filtro tendencia)");
   Print("ADX: ", ADX_Period, " períodos, máximo: ", ADX_Max, " (fuerza tendencia)");
   Print("MACD: ", MACD_Fast, "/", MACD_Slow, "/", MACD_Signal, " (dirección momentum)");
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
   if(RSI_Handle != INVALID_HANDLE)
      IndicatorRelease(RSI_Handle);
   if(EMA_Handle != INVALID_HANDLE)
      IndicatorRelease(EMA_Handle);
   if(ADX_Handle != INVALID_HANDLE)
      IndicatorRelease(ADX_Handle);
   if(MACD_Handle != INVALID_HANDLE)
      IndicatorRelease(MACD_Handle);
   
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
   
   // Copiar datos de RSI
   if(CopyBuffer(RSI_Handle, 0, 0, 3, RSI_Buffer) < 3)
      return;
   
   RSI_Value = RSI_Buffer[1];
   
   // Copiar datos de EMA
   if(CopyBuffer(EMA_Handle, 0, 0, 3, EMA_Buffer) < 3)
      return;
   
   EMA_Value = EMA_Buffer[1];
   
   // Copiar datos de ADX
   if(CopyBuffer(ADX_Handle, 0, 0, 3, ADX_Buffer) < 3)
      return;
   
   ADX_Value = ADX_Buffer[1];
   
   // Copiar datos de MACD
   if(CopyBuffer(MACD_Handle, 0, 0, 3, MACD_Main_Buffer) < 3)
      return;
   if(CopyBuffer(MACD_Handle, 1, 0, 3, MACD_Signal_Buffer) < 3)
      return;
   
   MACD_Main = MACD_Main_Buffer[1];
   MACD_Signal_Value = MACD_Signal_Buffer[1];
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
      // FILTROS: No operar BUY si hay tendencia alcista fuerte
      bool rsi_filter = (RSI_Value < RSI_Overbought); // RSI no en sobrecompra
      bool ema_filter = (close < EMA_Value); // Precio por debajo de EMA (no tendencia alcista)
      bool adx_filter = (ADX_Value < ADX_Max); // Tendencia débil (ADX < 25)
      bool macd_filter = (MACD_Main > MACD_Signal_Value); // Momentum alcista
      
      if(rsi_filter && ema_filter && adx_filter && macd_filter)
      {
         // Operación 1: Rápida (ratio 1:2)
         double sl1 = close - (ATR_Value * StopLoss_ATR_Mult);
         double tp1 = close + (ATR_Value * TakeProfit_Quick_ATR);
         ticket_quick = OpenOrder(ORDER_TYPE_BUY, LotSize, sl1, tp1, "BB Reversion Quick Buy");
         Print("Reversión BUY Rápida: TP 1:2 - RSI: ", RSI_Value, " EMA: ", EMA_Value, " ADX: ", ADX_Value, " MACD: ", MACD_Main, " - Ticket: ", ticket_quick);
         
         // Operación 2: Con trailing stop
         if(ticket_quick != 0)
         {
            double sl2 = close - (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close + (ATR_Value * TakeProfit_ATR_Mult);
            ticket_trailing = OpenOrder(ORDER_TYPE_BUY, LotSize, sl2, tp2, "BB Reversion Trailing Buy");
            Print("Reversión BUY Trailing: TP largo - Ticket: ", ticket_trailing);
         }
      }
      else
      {
         Print("BUY filtrado - RSI: ", RSI_Value, " (max ", RSI_Overbought, ") - EMA: ", close, " vs ", EMA_Value, " - ADX: ", ADX_Value, " (max ", ADX_Max, ") - MACD: ", MACD_Main, " vs ", MACD_Signal_Value);
      }
   }
   // Señal de reversión bajista: precio toca banda superior
   else if(high >= BB_Upper)
   {
      // FILTROS: No operar SELL si hay tendencia bajista fuerte
      bool rsi_filter = (RSI_Value > RSI_Oversold); // RSI no en sobrevenda
      bool ema_filter = (close > EMA_Value); // Precio por encima de EMA (no tendencia bajista)
      bool adx_filter = (ADX_Value < ADX_Max); // Tendencia débil (ADX < 25)
      bool macd_filter = (MACD_Main < MACD_Signal_Value); // Momentum bajista
      
      if(rsi_filter && ema_filter && adx_filter && macd_filter)
      {
         // Operación 1: Rápida (ratio 1:2)
         double sl1 = close + (ATR_Value * StopLoss_ATR_Mult);
         double tp1 = close - (ATR_Value * TakeProfit_Quick_ATR);
         ticket_quick = OpenOrder(ORDER_TYPE_SELL, LotSize, sl1, tp1, "BB Reversion Quick Sell");
         Print("Reversión SELL Rápida: TP 1:2 - RSI: ", RSI_Value, " EMA: ", EMA_Value, " ADX: ", ADX_Value, " MACD: ", MACD_Main, " - Ticket: ", ticket_quick);
         
         // Operación 2: Con trailing stop
         if(ticket_quick != 0)
         {
            double sl2 = close + (ATR_Value * StopLoss_ATR_Mult);
            double tp2 = close - (ATR_Value * TakeProfit_ATR_Mult);
            ticket_trailing = OpenOrder(ORDER_TYPE_SELL, LotSize, sl2, tp2, "BB Reversion Trailing Sell");
            Print("Reversión SELL Trailing: TP largo - Ticket: ", ticket_trailing);
         }
      }
      else
      {
         Print("SELL filtrado - RSI: ", RSI_Value, " (min ", RSI_Oversold, ") - EMA: ", close, " vs ", EMA_Value, " - ADX: ", ADX_Value, " (max ", ADX_Max, ") - MACD: ", MACD_Main, " vs ", MACD_Signal_Value);
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
   
   double close = iClose(_Symbol, PERIOD_M1, 0);
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double tp = PositionGetDouble(POSITION_TP);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   // Verificar si alcanzó el TP (ratio 1:2)
   if(posType == POSITION_TYPE_BUY)
   {
      if(close >= tp)
      {
         ClosePosition(ticket_quick);
         Print("Operación BUY Rápida cerrada por TP 1:2 - Ticket: ", ticket_quick);
         ticket_quick = 0;
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      if(close <= tp)
      {
         ClosePosition(ticket_quick);
         Print("Operación SELL Rápida cerrada por TP 1:2 - Ticket: ", ticket_quick);
         ticket_quick = 0;
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
            if(StringFind(comment, "Quick") != -1)
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
