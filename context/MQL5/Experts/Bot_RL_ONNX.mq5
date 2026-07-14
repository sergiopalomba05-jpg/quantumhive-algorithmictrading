//+------------------------------------------------------------------+
//|                                              Bot_RL_ONNX.mq5    |
//|  EA para Strategy Tester con modelo ONNX exportado desde Python  |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Math\Stat\Stat.mqh>

input group "=== Modelo ONNX ==="
input string OnnxFileName = "bot_unificado.onnx";  // Nombre del archivo ONNX (debe estar en MQL5/Files/)

input group "=== Parámetros de Trading ==="
input double   LotSize = 0.1;
input double   SlAtrMult = 2.0;
input double   Tp1AtrMult = 1.5;
input double   Tp2AtrMult = 3.0;
input int      BbPeriod = 20;
input double   BbDev = 2.0;
input int      RsiPeriod = 14;
input int      AtrPeriod = 14;
input int      EmaPeriod = 50;
input double   RiskPct = 0.01;
input int      MaxOpsDay = 2;
input int      VentanaApertura = 26;  // barras desde inicio del día
input int      MagicNumber = 123456;

input group "=== Horario ==="
input int      NYStartHour = 14;
input int      NYEndHour = 21;

//--- Handles de indicadores
int hBB, hRSI, hATR, hEMA;

//--- Estado del modelo ONNX
long onnxHandle = INVALID_HANDLE;

//--- Estado de trading
struct TradeState {
   bool   posAbierta;
   int    direccion;      // 1=Buy, -1=Sell, 0=none
   double precioEntrada;
   double sl;
   double tp1;
   double tp2;
   double loteTotal;
   double loteRemanente;
   bool   beActivado;
   string modo;
   int    opsHoy;
   double pnlDia;
   int    barrasDesdeInicioDia;
   datetime fechaEquityDia;
};
TradeState ts;

//--- Objetos de trading
CTrade trade;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- Cargar modelo ONNX
   string onnxPath = OnnxFileName;
   if(!FileIsExist(onnxPath))
   {
      // Intentar en directorio común
      onnxPath = "Models\\" + OnnxFileName;
      if(!FileIsExist(onnxPath))
      {
         Print("[ERROR] No se encuentra el modelo ONNX: ", OnnxFileName);
         Print("Coloca el archivo en: MQL5/Files/ o MQL5/Files/Models/");
         return INIT_FAILED;
      }
   }
   
   onnxHandle = OnnxCreate(onnxPath);
   if(onnxHandle == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudo cargar modelo ONNX: ", onnxPath);
      return INIT_FAILED;
   }
   
   //--- Configurar inputs/outputs del modelo
   // El modelo espera input: float32[batch, 10]
   // output: float32[batch, 7] (logits de 7 acciones)
   if(!OnnxSetInputShape(onnxHandle, 0, 1, 10))
   {
      Print("[ERROR] No se pudo configurar input shape");
      OnnxRelease(onnxHandle);
      return INIT_FAILED;
   }
   
   //--- Crear indicadores
   hBB = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE);
   hRSI = iRSI(_Symbol, PERIOD_M15, RsiPeriod, PRICE_CLOSE);
   hATR = iATR(_Symbol, PERIOD_M15, AtrPeriod);
   hEMA = iMA(_Symbol, PERIOD_M15, EmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   
   if(hBB == INVALID_HANDLE || hRSI == INVALID_HANDLE || hATR == INVALID_HANDLE || hEMA == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudieron crear los indicadores");
      OnnxRelease(onnxHandle);
      return INIT_FAILED;
   }
   
   //--- Configurar trading
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   trade.SetAsyncMode(false);
   
   //--- Resetear estado
   ResetTradeState();
   
   Print("[OK] Bot_RL_ONNX inicializado. Modelo: ", onnxPath);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(onnxHandle != INVALID_HANDLE)
      OnnxRelease(onnxHandle);
   
   IndicatorRelease(hBB);
   IndicatorRelease(hRSI);
   IndicatorRelease(hATR);
   IndicatorRelease(hEMA);
   
   Print("[OK] Bot_RL_ONNX finalizado. Razón: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Solo operar en timeframe M15
   if(Period() != PERIOD_M15) return;
   
   //--- Verificar horario NY (14-21h)
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);
   if(dt.hour < NYStartHour || dt.hour > NYEndHour) return;
   
   //--- Nueva vela?
   static datetime lastBarTime = 0;
   if(lastBarTime == iTime(_Symbol, PERIOD_M15, 0)) return;
   lastBarTime = iTime(_Symbol, PERIOD_M15, 0);
   
   //--- Actualizar contadores diarios
   if(ts.fechaEquityDia != dt.day)
   {
      ts.fechaEquityDia = dt.day;
      ts.opsHoy = 0;
      ts.pnlDia = 0;
      ts.barrasDesdeInicioDia = 0;
   }
   else
   {
      ts.barrasDesdeInicioDia++;
   }
   
   //--- Obtener precios M15
   double c = iClose(_Symbol, PERIOD_M15, 1);
   double o = iOpen(_Symbol, PERIOD_M15, 1);
   double h = iHigh(_Symbol, PERIOD_M15, 1);
   double l = iLow(_Symbol, PERIOD_M15, 1);
   
   //--- Calcular indicadores M15
   double bbUpper = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_UPPER, 1);
   double bbLower = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_LOWER, 1);
   double bbMain = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_MAIN, 1);
   double rsi = iRSI(_Symbol, PERIOD_M15, RsiPeriod, PRICE_CLOSE, 1);
   double atr = iATR(_Symbol, PERIOD_M15, AtrPeriod, 1);
   double ema50 = iMA(_Symbol, PERIOD_M15, EmaPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema50Prev = iMA(_Symbol, PERIOD_M15, EmaPeriod, 0, MODE_EMA, PRICE_CLOSE, 2);
   
   if(bbUpper == 0 || bbLower == 0 || rsi == 0 || atr == 0) return;
   
   //--- Calcular %B
   double pb = (c - bbLower) / MathMax(1e-12, bbUpper - bbLower);
   
   //--- Calcular BBW estado
   double bbw = (bbUpper - bbLower) / MathMax(1e-12, bbMain);
   
   // Calcular percentiles aproximados de BBW (usando histórico reciente)
   double bbwHist[50];
   for(int i = 0; i < 50; i++)
   {
      double u = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_UPPER, i+1);
      double m = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_MAIN, i+1);
      double lo = iBands(_Symbol, PERIOD_M15, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_LOWER, i+1);
      bbwHist[i] = (u - lo) / MathMax(1e-12, m);
   }
   ArraySort(bbwHist);
   double bbwP20 = bbwHist[9];   // ~20th percentile
   double bbwP80 = bbwHist[39];  // ~80th percentile
   
   double bbwEst = 0.0;
   if(bbw > bbwP80) bbwEst = 1.0;
   else if(bbw < bbwP20) bbwEst = -1.0;
   
   //--- Pendiente EMA
   double pendEma = (ema50 - ema50Prev);
   
   //--- Calcular confluencia M5 y M1
   double confM5 = CalcularConfluencia(PERIOD_M5, 1);
   double confM1 = CalcularConfluencia(PERIOD_M1, 1);
   
   //--- Tendencia H1
   double ema50H1 = iMA(_Symbol, PERIOD_H1, EmaPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double cH1 = iClose(_Symbol, PERIOD_H1, 1);
   double tendH1 = MathSign(cH1 - ema50H1);
   if(tendH1 == 0) tendH1 = 0;
   
   //--- Estado posición
   double posEstado = 0.0;
   if(ts.posAbierta)
      posEstado = (ts.direccion == 1) ? 1.0 : -1.0;
   
   //--- PnL normalizado
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double pnlNorm = MathMax(-1, MathMin(1, ts.pnlDia / MathMax(1e-12, balance) * 10));
   
   //--- Construir observación [1, 10]
   float obs[10];
   obs[0] = (float)MathMax(-1, MathMin(1, pb * 2 - 1));
   obs[1] = (float)MathMax(-1, MathMin(1, rsi / 50 - 1));
   obs[2] = (float)MathMax(-1, MathMin(1, bbwEst));
   obs[3] = (float)MathMax(-1, MathMin(1, pendEma * 1000));
   obs[4] = (float)confM5;
   obs[5] = (float)confM1;
   obs[6] = (float)tendH1;
   obs[7] = (float)MathMax(-1, MathMin(1, atr / c * 100));
   obs[8] = (float)posEstado;
   obs[9] = (float)pnlNorm;
   
   //--- Predecir acción con ONNX
   float output[7];
   if(!OnnxRun(onnxHandle, 1, obs, output))
   {
      Print("[ERROR] OnnxRun falló");
      return;
   }
   
   //--- Elegir acción (argmax de logits)
   int action = 0;
   float maxLogit = output[0];
   for(int i = 1; i < 7; i++)
   {
      if(output[i] > maxLogit)
      {
         maxLogit = output[i];
         action = i;
      }
   }
   
   //--- Ejecutar acción
   // action: 0=Hold, 1=REV Buy, 2=REV Sell, 3=CONT Buy, 4=CONT Sell, 5=SCALP Buy, 6=SCALP Sell
   if(action != 0 && !ts.posAbierta && ts.opsHoy < MaxOpsDay)
   {
      string modo = "";
      int dir = 0;
      
      if(action == 1)      { modo = "REV"; dir = 1; }
      else if(action == 2) { modo = "REV"; dir = -1; }
      else if(action == 3) { modo = "CONT"; dir = 1; }
      else if(action == 4) { modo = "CONT"; dir = -1; }
      else if(action == 5) { modo = "SCALP"; dir = 1; }
      else if(action == 6) { modo = "SCALP"; dir = -1; }
      
      //--- Evaluar condiciones de apertura (simplificado)
      double conf = CalcularConfluenciaScore(c, o, h, l, bbUpper, bbLower, rsi, dir);
      
      bool momentum = MathAbs(pendEma) > 0.0002;
      bool tendFavor = (dir == 1 && tendH1 >= 0) || (dir == -1 && tendH1 <= 0);
      
      bool abrir = false;
      if(StringFind(modo, "REV") >= 0)
         abrir = (conf >= 0.5);
      else if(StringFind(modo, "CONT") >= 0)
         abrir = (rsi >= 45 && rsi <= 75 && tendFavor && momentum && dir == 1) || 
                 (rsi >= 25 && rsi <= 55 && tendFavor && momentum && dir == -1);
      else if(StringFind(modo, "SCALP") >= 0)
         abrir = (conf >= 0.5 && momentum);
      
      if(abrir)
      {
         double slOffset = atr * SlAtrMult;
         double tp1Offset = atr * Tp1AtrMult;
         double tp2Offset = atr * Tp2AtrMult;
         
         double slPrice, tp1Price, tp2Price;
         if(dir == 1)
         {
            slPrice = c - slOffset;
            tp1Price = c + tp1Offset;
            tp2Price = c + tp2Offset;
         }
         else
         {
            slPrice = c + slOffset;
            tp1Price = c - tp1Offset;
            tp2Price = c - tp2Offset;
         }
         
         // Calcular lotaje basado en riesgo
         double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
         double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
         double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
         double slPoints = MathAbs(slPrice - c) / point;
         double riskAmount = balance * RiskPct;
         double lots = riskAmount / (slPoints * point * tickValue / tickSize);
         lots = MathMax(0.01, MathMin(lots, 5.0));
         lots = NormalizeDouble(lots, 2);
         
         if(dir == 1)
            trade.Buy(lots, _Symbol, 0, slPrice, tp2Price, "RL_" + modo);
         else
            trade.Sell(lots, _Symbol, 0, slPrice, tp2Price, "RL_" + modo);
         
         if(trade.ResultRetcode() == TRADE_RETCODE_DONE)
         {
            ts.posAbierta = true;
            ts.direccion = dir;
            ts.precioEntrada = c;
            ts.sl = slPrice;
            ts.tp1 = tp1Price;
            ts.tp2 = tp2Price;
            ts.loteTotal = lots;
            ts.loteRemanente = lots;
            ts.beActivado = false;
            ts.modo = modo;
            ts.opsHoy++;
         }
      }
   }
   
   //--- Gestionar posición abierta
   if(ts.posAbierta)
   {
      GestionarPosicion(h, l);
   }
}

//+------------------------------------------------------------------+
//| Calcular confluencia para un timeframe                            |
//+------------------------------------------------------------------+
double CalcularConfluencia(ENUM_TIMEFRAMES tf, int shift)
{
   double c = iClose(_Symbol, tf, shift);
   double o = iOpen(_Symbol, tf, shift);
   double h = iHigh(_Symbol, tf, shift);
   double l = iLow(_Symbol, tf, shift);
   
   double bbU = iBands(_Symbol, tf, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_UPPER, shift);
   double bbL = iBands(_Symbol, tf, BbPeriod, 0, BbDev, PRICE_CLOSE, MODE_LOWER, shift);
   double rsiTf = iRSI(_Symbol, tf, RsiPeriod, PRICE_CLOSE, shift);
   
   if(bbU == 0 || bbL == 0) return 0;
   
   return CalcularConfluenciaScore(c, o, h, l, bbU, bbL, rsiTf, 0);
}

//+------------------------------------------------------------------+
//| Calcular score de confluencia (direccion=0 para neutro)           |
//+------------------------------------------------------------------+
double CalcularConfluenciaScore(double c, double o, double h, double l, 
                                 double bbSup, double bbInf, double rsi, int direccion)
{
   double rango = MathMax(1e-12, h - l);
   double score = 0.0;
   
   if(direccion == 1) // Compra
   {
      bool tocaInf = l <= bbInf;
      bool rsiExtremo = rsi < 20;
      bool mechaRev = false;
      if(o > c)
         mechaRev = (o - l) / rango > 0.35;
      else
         mechaRev = (c - l) / rango > 0.35;
      
      if(tocaInf && rsiExtremo && mechaRev)
         score = 0.7;
      else if(tocaInf && rsi < 25)
         score = 0.35;
      else if(l <= bbInf + (bbSup - bbInf) * 0.05 && rsi < 25)
         score = 0.2;
   }
   else if(direccion == -1) // Venta
   {
      bool tocaSup = h >= bbSup;
      bool rsiExtremo = rsi > 80;
      bool mechaRev = false;
      if(o < c)
         mechaRev = (h - o) / rango > 0.35;
      else
         mechaRev = (h - c) / rango > 0.35;
      
      if(tocaSup && rsiExtremo && mechaRev)
         score = 0.7;
      else if(tocaSup && rsi > 75)
         score = 0.35;
      else if(h >= bbSup - (bbSup - bbInf) * 0.05 && rsi > 75)
         score = 0.2;
   }
   else // Neutro
   {
      double distSup = (bbSup - c) / MathMax(1e-12, bbSup - bbInf);
      double distInf = (c - bbInf) / MathMax(1e-12, bbSup - bbInf);
      if(distSup < 0.15 || distInf < 0.15)
         score = 0.3;
      else if(distSup < 0.3 || distInf < 0.3)
         score = 0.15;
      if(rsi > 80 || rsi < 20)
         score += 0.2;
   }
   
   return MathMax(0.0, MathMin(1.0, score));
}

//+------------------------------------------------------------------+
//| Gestionar posición abierta                                         |
//+------------------------------------------------------------------+
void GestionarPosicion(double high, double low)
{
   //--- Verificar SL/TP
   if(ts.direccion == 1) // Long
   {
      if(low <= ts.sl)
      {
         CerrarPosicion("sl");
         return;
      }
      if(!ts.beActivado && high >= ts.tp1)
      {
         // Cierre parcial + BE
         CerrarParcial();
         return;
      }
      if(high >= ts.tp2)
      {
         CerrarPosicion("tp2");
         return;
      }
   }
   else // Short
   {
      if(high >= ts.sl)
      {
         CerrarPosicion("sl");
         return;
      }
      if(!ts.beActivado && low <= ts.tp1)
      {
         CerrarParcial();
         return;
      }
      if(low <= ts.tp2)
      {
         CerrarPosicion("tp2");
         return;
      }
   }
}

//+------------------------------------------------------------------+
//| Cerrar posición completa                                           |
//+------------------------------------------------------------------+
void CerrarPosicion(string motivo)
{
   double pnl = 0;
   if(ts.direccion == 1)
      pnl = (SymbolInfoDouble(_Symbol, SYMBOL_BID) - ts.precioEntrada) * ts.loteRemanente;
   else
      pnl = (ts.precioEntrada - SymbolInfoDouble(_Symbol, SYMBOL_ASK)) * ts.loteRemanente;
   
   ts.pnlDia += pnl;
   
   trade.PositionClose(_Symbol);
   ResetTradeState();
}

//+------------------------------------------------------------------+
//| Cerrar parcial y mover SL a BE                                     |
//+------------------------------------------------------------------+
void CerrarParcial()
{
   double closePrice = (ts.direccion == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double pnl = 0;
   if(ts.direccion == 1)
      pnl = (closePrice - ts.precioEntrada) * ts.loteTotal * 0.5;
   else
      pnl = (ts.precioEntrada - closePrice) * ts.loteTotal * 0.5;
   
   ts.pnlDia += pnl;
   ts.loteRemanente *= 0.5;
   ts.sl = ts.precioEntrada;
   ts.beActivado = true;
   
   // Cerrar mitad
   trade.PositionClosePartial(_Symbol, ts.loteTotal * 0.5);
}

//+------------------------------------------------------------------+
//| Resetear estado de trading                                         |
//+------------------------------------------------------------------+
void ResetTradeState()
{
   ts.posAbierta = false;
   ts.direccion = 0;
   ts.precioEntrada = 0;
   ts.sl = 0;
   ts.tp1 = 0;
   ts.tp2 = 0;
   ts.loteTotal = 0;
   ts.loteRemanente = 0;
   ts.beActivado = false;
   ts.modo = "";
}

//+------------------------------------------------------------------+
//| Signo de un número                                                 |
//+------------------------------------------------------------------+
double MathSign(double x)
{
   if(x > 0) return 1;
   if(x < 0) return -1;
   return 0;
}
//+------------------------------------------------------------------+
