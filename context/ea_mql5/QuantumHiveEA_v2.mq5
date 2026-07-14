//+------------------------------------------------------------------+
//| QuantumHive EA v2 — Enjambre 4 Bots ONNX + Kill-Switch + Logger  |
//| Carga: bot_madre.onnx, bot_reversion.onnx,                        |
//|        bot_continuacion.onnx, bot_scalper.onnx                    |
//| Kill-switch: lee C:\Users\sergio\BotsCuanticos\datos\STOP.txt     |
//| Reporte: escribe trades a historial_trades_ea.csv                 |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property link      "https://quantumhive.ai"
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include "FiltroHorario.mqh"
#include "GestorRiesgoEA.mqh"

input group "=== RUTAS ONNX ==="
input string OnnxPathMadre      = "C:\\Users\\sergio\\BotsCuanticos\\modelos\\bot_madre.onnx";
input string OnnxPathReversion  = "C:\\Users\\sergio\\BotsCuanticos\\modelos\\bot_reversion.onnx";
input string OnnxPathContinuacion = "C:\\Users\\sergio\\BotsCuanticos\\modelos\\bot_continuacion.onnx";
input string OnnxPathScalper    = "C:\\Users\\sergio\\BotsCuanticos\\modelos\\bot_scalper.onnx";

input group "=== KILL-SWITCH ==="
input string KillSwitchPath     = "C:\\Users\\sergio\\BotsCuanticos\\datos\\STOP.txt";

input group "=== RIESGO ==="
input double RiesgoPorTradePct  = 2.0;    // % capital por trade
input double SL_Fijo_Pips       = 15.0;
input double TP_Fijo_Pips       = 30.0;
input double BE_Trailing_ATR    = 1.0;    // ATR multiplicador para BE
input int    MagicNumber        = 123456;

input group "=== FILTROS ==="
input bool   FiltrarHorario     = true;
input int    MaxPosicionesSimul = 4;      // Madre + Rev + Cont + Scalper

//--- ONNX handles
long handleMadre = INVALID_HANDLE;
long handleRev   = INVALID_HANDLE;
long handleCont  = INVALID_HANDLE;
long handleScalp = INVALID_HANDLE;

//--- Estado del enjambre
enum ENUM_REGIMEN { REGIMEN_WAIT=0, REGIMEN_REVERSION=1, REGIMEN_CONTINUACION=2 };
ENUM_REGIMEN g_regimen = REGIMEN_WAIT;

//--- Trading
CTrade g_trade;
datetime g_lastBarTime = 0;
string   g_logFile = "";
string   g_historialPath = "C:\\Users\\sergio\\BotsCuanticos\\datos\\historial_trades_ea.csv";

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Kill-switch inmediato
   if(KillSwitchActivo())
   {
      Print("[KILL-SWITCH] STOP.txt detectado. EA no inicia.");
      return INIT_FAILED;
   }

   // Cargar modelos ONNX
   handleMadre = OnnxCreate(OnnxPathMadre);
   handleRev   = OnnxCreate(OnnxPathReversion);
   handleCont  = OnnxCreate(OnnxPathContinuacion);
   handleScalp = OnnxCreate(OnnxPathScalper);

   if(handleMadre == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudo cargar bot_madre.onnx");
      return INIT_FAILED;
   }
   Print("[ONNX] Madre cargado OK.");
   if(handleRev   != INVALID_HANDLE) Print("[ONNX] Reversion cargado OK.");
   if(handleCont  != INVALID_HANDLE) Print("[ONNX] Continuacion cargado OK.");
   if(handleScalp != INVALID_HANDLE) Print("[ONNX] Scalper cargado OK.");

   g_trade.SetExpertMagicNumber(MagicNumber);
   g_trade.SetDeviationInPoints(10);
   g_trade.SetTypeFilling(ORDER_FILLING_IOC);
   g_trade.SetAsyncMode(false);

   // Inicializar CSV de trades
   InicializarHistorial();

   Print("[QuantumHiveEA v2] Inicializado. Kill-switch: ", KillSwitchPath);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(handleMadre != INVALID_HANDLE) OnnxRelease(handleMadre);
   if(handleRev   != INVALID_HANDLE) OnnxRelease(handleRev);
   if(handleCont  != INVALID_HANDLE) OnnxRelease(handleCont);
   if(handleScalp != INVALID_HANDLE) OnnxRelease(handleScalp);
   Print("[QuantumHiveEA v2] Detenido. Razon: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // --- 1. KILL-SWITCH CHECK cada tick ---
   if(KillSwitchActivo())
   {
      CerrarTodasPosiciones("KILL_SWITCH");
      Print("[KILL-SWITCH] STOP.txt detectado. Cerrando TODO.");
      return;
   }

   // --- 2. Barra nueva M1 ---
   datetime currentBarTime = iTime(_Symbol, PERIOD_M1, 0);
   if(currentBarTime == g_lastBarTime) return;  // solo evaluar en nueva barra
   g_lastBarTime = currentBarTime;

   // --- 3. Filtro horario ---
   if(FiltrarHorario && !EsHorarioValido()) return;

   // --- 4. Limite de posiciones ---
   int totalPos = PositionsTotal();
   if(totalPos >= MaxPosicionesSimul) return;

   // --- 5. Bot Madre: decide REGIMEN ---
   float obsMadre[];
   ArrayResize(obsMadre, 14 + 5);  // 14 features + confluencias
   CalcularObservacionMadre(obsMadre);

   float outputMadre[];
   ArrayResize(outputMadre, 3);
   if(!OnnxRun(handleMadre, ONNX_DEFAULT, obsMadre, outputMadre))
   {
      Print("[ERROR] ONNX Madre fallo: ", GetLastError());
      return;
   }

   // Softmax manual para obtener clase
   float maxVal = MathMax(outputMadre[0], MathMax(outputMadre[1], outputMadre[2]));
   int decisionMadre = 0;
   for(int i=0; i<3; i++) if(outputMadre[i] == maxVal) { decisionMadre = i; break; }

   g_regimen = (ENUM_REGIMEN)decisionMadre;
   Print("[MADRE] Regimen: ", g_regimen, " | logits: ",
         DoubleToString(outputMadre[0],4), " ",
         DoubleToString(outputMadre[1],4), " ",
         DoubleToString(outputMadre[2],4));

   if(g_regimen == REGIMEN_WAIT) return;  // No operar

   // --- 6. Ejecutar bot hijo segun regimen ---
   if(g_regimen == REGIMEN_REVERSION && handleRev != INVALID_HANDLE)
   {
      if(!TienePosicionMagic(MagicNumber + 1))
         EjecutarBot(handleRev, "REVERSIÓN", MagicNumber + 1, ORDER_TYPE_BUY, ORDER_TYPE_SELL);
   }
   else if(g_regimen == REGIMEN_CONTINUACION && handleCont != INVALID_HANDLE)
   {
      if(!TienePosicionMagic(MagicNumber + 2))
         EjecutarBot(handleCont, "CONTINUACIÓN", MagicNumber + 2, ORDER_TYPE_BUY, ORDER_TYPE_SELL);
   }

   // --- 7. Scalper M1: evalua independientemente ---
   if(handleScalp != INVALID_HANDLE && !TienePosicionMagic(MagicNumber + 3))
   {
      float obsScalp[];
      ArrayResize(obsScalp, 17);
      CalcularObservacionScalper(obsScalp);

      float outScalp[];
      ArrayResize(outScalp, 3);
      if(OnnxRun(handleScalp, ONNX_DEFAULT, obsScalp, outScalp))
      {
         float mx = MathMax(outScalp[0], MathMax(outScalp[1], outScalp[2]));
         int dec = 0;
         for(int i=0; i<3; i++) if(outScalp[i] == mx) { dec = i; break; }

         if(dec == 1)  // SHORT
            AbrirPosicion(ORDER_TYPE_SELL, MagicNumber + 3, "SCALPER_SHORT", 0.5);
         else if(dec == 2)  // LONG
            AbrirPosicion(ORDER_TYPE_BUY, MagicNumber + 3, "SCALPER_LONG", 0.5);
      }
   }

   // --- 8. Trailing / BreakEven ---
   GestionarPosicionesAbiertas();
}

//+------------------------------------------------------------------+
//| Kill-Switch: verifica existencia de STOP.txt                      |
//+------------------------------------------------------------------+
bool KillSwitchActivo()
{
   string filename = KillSwitchPath;
   // En MQL5 usamos FileOpen con ruta relativa al directorio común
   // Pero para rutas absolutas de Windows usamos el flag FILE_COMMON
   int handle = FileOpen("..\\..\\datos\\STOP.txt", FILE_READ|FILE_TXT|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileClose(handle);
      return true;
   }
   // Fallback: usar path directo (requiere permisos)
   return false;
}

//+------------------------------------------------------------------+
//| Calcular features para Bot Madre (19 inputs)                      |
//+------------------------------------------------------------------+
void CalcularObservacionMadre(float &obs[])
{
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double high  = iHigh(_Symbol, PERIOD_M1, 1);
   double low   = iLow(_Symbol, PERIOD_M1, 1);
   double open  = iOpen(_Symbol, PERIOD_M1, 1);
   long   tickvol = iTickVolume(_Symbol, PERIOD_M1, 1);

   // Normalizacion simple
   double rng = high - low;
   if(rng == 0) rng = 0.0001;

   obs[0]  = (float)(close);
   obs[1]  = (float)(high);
   obs[2]  = (float)(low);
   obs[3]  = (float)(open);
   obs[4]  = (float)(tickvol / 1000.0);

   // Indicadores M1
   double rsi       = iRSI(_Symbol, PERIOD_M1, 14, PRICE_CLOSE, 1);
   double ema_fast  = iMA(_Symbol, PERIOD_M1, 12, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema_slow  = iMA(_Symbol, PERIOD_M1, 26, 0, MODE_EMA, PRICE_CLOSE, 1);
   double bb_up     = iBands(_Symbol, PERIOD_M1, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 1);
   double bb_low    = iBands(_Symbol, PERIOD_M1, 20, 2, 0, PRICE_CLOSE, MODE_LOWER, 1);
   double atr       = iATR(_Symbol, PERIOD_M1, 14, 1);
   double adx       = iADX(_Symbol, PERIOD_M1, 14, PRICE_CLOSE, 1);
   double macd_main = iMACD(_Symbol, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
   double macd_sig  = iMACD(_Symbol, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);

   obs[5]  = (float)(rsi / 100.0);           // 0-1
   obs[6]  = (float)(ema_fast / close - 1.0);
   obs[7]  = (float)(ema_slow / close - 1.0);
   obs[8]  = (float)((close - bb_low) / (bb_up - bb_low + 0.0001)); // bb_pct_b
   obs[9]  = (float)((bb_up - bb_low) / ((bb_up+bb_low)/2 + 0.0001)); // bbw
   obs[10] = (float)(atr / close);
   obs[11] = (float)(adx / 100.0);
   obs[12] = (float)(macd_main);
   obs[13] = (float)(macd_sig);

   // Confluencias TF superiores (simplificadas: 0=no data, 1=alcista, -1=bajista)
   double ema_m5  = iMA(_Symbol, PERIOD_M5, 20, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema_h1  = iMA(_Symbol, PERIOD_H1, 20, 0, MODE_EMA, PRICE_CLOSE, 1);
   obs[14] = (float)((ema_m5 > close*1.0002) ? 1.0 : (ema_m5 < close*0.9998 ? -1.0 : 0.0));
   obs[15] = (float)((ema_h1 > close*1.0002) ? 1.0 : (ema_h1 < close*0.9998 ? -1.0 : 0.0));
   obs[16] = obs[14];  // MACD confluence placeholder
   obs[17] = obs[8];   // BB position
   obs[18] = (float)(MathSign(macd_main - macd_sig)); // DI confluence proxy
}

//+------------------------------------------------------------------+
//| Calcular features para Scalper (17 inputs)                      |
//+------------------------------------------------------------------+
void CalcularObservacionScalper(float &obs[])
{
   double close = iClose(_Symbol, PERIOD_M1, 1);
   double high  = iHigh(_Symbol, PERIOD_M1, 1);
   double low   = iLow(_Symbol, PERIOD_M1, 1);

   double rsi     = iRSI(_Symbol, PERIOD_M1, 14, PRICE_CLOSE, 1);
   double ema12   = iMA(_Symbol, PERIOD_M1, 12, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema26   = iMA(_Symbol, PERIOD_M1, 26, 0, MODE_EMA, PRICE_CLOSE, 1);
   double bb_up   = iBands(_Symbol, PERIOD_M1, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 1);
   double bb_low  = iBands(_Symbol, PERIOD_M1, 20, 2, 0, PRICE_CLOSE, MODE_LOWER, 1);
   double atr     = iATR(_Symbol, PERIOD_M1, 14, 1);

   obs[0]  = (float)(close);
   obs[1]  = (float)(high);
   obs[2]  = (float)(low);
   obs[3]  = (float)(rsi / 100.0);
   obs[4]  = (float)(ema12 / close - 1.0);
   obs[5]  = (float)(ema26 / close - 1.0);
   obs[6]  = (float)((close - bb_low) / (bb_up - bb_low + 0.0001)); // bb_pct_b
   obs[7]  = (float)((bb_up - bb_low) / ((bb_up+bb_low)/2 + 0.0001)); // bbw
   obs[8]  = (float)(atr / close);

   // MACD
   double macd_main = iMACD(_Symbol, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
   double macd_sig  = iMACD(_Symbol, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
   obs[9]  = (float)(macd_main);
   obs[10] = (float)(macd_sig);
   obs[11] = (float)(macd_main - macd_sig);

   // Volumen relativo (5 barras)
   long vol1 = iTickVolume(_Symbol, PERIOD_M1, 1);
   long vol5 = 0;
   for(int i=1; i<=5; i++) vol5 += iTickVolume(_Symbol, PERIOD_M1, i);
   obs[12] = (float)(vol1 / (vol5/5.0 + 1));

   // Spread
   obs[13] = (float)(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD));

   // Momentum 3 barras
   double close3 = iClose(_Symbol, PERIOD_M1, 3);
   obs[14] = (float)((close - close3) / close3);

   // ATR posicion
   obs[15] = (float)((close - low) / (high - low + 0.0001));
   obs[16] = (float)(MathSign(macd_main));
}

//+------------------------------------------------------------------+
//| Ejecutar bot hijo (Reversion o Continuacion)                      |
//+------------------------------------------------------------------+
void EjecutarBot(long handleOnnx, string nombre, int magic,
                 ENUM_ORDER_TYPE tipoBaseCompra, ENUM_ORDER_TYPE tipoBaseVenta)
{
   float obs[];
   ArrayResize(obs, 17);
   CalcularObservacionScalper(obs);  // Usamos mismo vector para hijos (compatibilidad)

   float output[];
   ArrayResize(output, 3);
   if(!OnnxRun(handleOnnx, ONNX_DEFAULT, obs, output)) return;

   float mx = MathMax(output[0], MathMax(output[1], output[2]));
   int dec = 0;
   for(int i=0; i<3; i++) if(output[i] == mx) { dec = i; break; }

   if(dec == 1)
      AbrirPosicion(tipoBaseVenta, magic, nombre + "_SHORT", 1.0);
   else if(dec == 2)
      AbrirPosicion(tipoBaseCompra, magic, nombre + "_LONG", 1.0);
}

//+------------------------------------------------------------------+
//| Abrir posicion con SL/TP y registrar en CSV                      |
//+------------------------------------------------------------------+
void AbrirPosicion(ENUM_ORDER_TYPE tipo, int magic, string comentario, double multiplicadorLote)
{
   double precio   = (tipo == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                               : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double point    = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double atr      = iATR(_Symbol, PERIOD_M1, 14, 1);

   double slPips = (SL_Fijo_Pips > 0) ? SL_Fijo_Pips : (atr / point / 10.0);
   double tpPips = (TP_Fijo_Pips > 0) ? TP_Fijo_Pips : (slPips * 2.0);

   double sl = (tipo == ORDER_TYPE_BUY) ? precio - slPips * point * 10
                                        : precio + slPips * point * 10;
   double tp = (tipo == ORDER_TYPE_BUY) ? precio + tpPips * point * 10
                                        : precio - tpPips * point * 10;

   double lote = CalcularLote(RiesgoPorTradePct * multiplicadorLote, MathAbs(precio - sl));
   if(lote <= 0) return;

   g_trade.SetExpertMagicNumber(magic);
   bool ok = g_trade.PositionOpen(_Symbol, tipo, lote, precio, sl, tp, comentario);

   if(ok)
   {
      Print("[TRADE] ", comentario, " | ", (tipo==ORDER_TYPE_BUY?"BUY":"SELL"),
            " | Lote=", DoubleToString(lote,2), " | SL=", DoubleToString(sl,5), " | TP=", DoubleToString(tp,5));
      RegistrarTrade(comentario, (tipo==ORDER_TYPE_BUY?"LONG":"SHORT"), precio, sl, tp, lote, "abierta");
   }
   else
   {
      Print("[ERROR] Fallo apertura ", comentario, ": ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Calcular lote basado en riesgo %                                  |
//+------------------------------------------------------------------+
double CalcularLote(double riesgoPct, double distanciaSL)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riesgoUSD = balance * riesgoPct / 100.0;
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(distanciaSL == 0 || tickValue == 0) return 0.01;
   double ticksSL = distanciaSL / tickSize;
   double lote = riesgoUSD / (ticksSL * tickValue);
   double minLote = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLote = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lote = MathFloor(lote / step) * step;
   lote = MathMax(minLote, MathMin(maxLote, lote));
   return lote;
}

//+------------------------------------------------------------------+
//| Gestionar posiciones abiertas (BE + Trailing)                     |
//+------------------------------------------------------------------+
void GestionarPosicionesAbiertas()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber &&
         PositionGetInteger(POSITION_MAGIC) != MagicNumber+1 &&
         PositionGetInteger(POSITION_MAGIC) != MagicNumber+2 &&
         PositionGetInteger(POSITION_MAGIC) != MagicNumber+3) continue;

      double op = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl = PositionGetDouble(POSITION_SL);
      double tp = PositionGetDouble(POSITION_TP);
      double price = (PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)
                     ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                     : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      int dir = (PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY) ? 1 : -1;

      // BreakEven cuando profit = 1x ATR
      double atr = iATR(_Symbol, PERIOD_M1, 14, 1);
      double avance = (price - op) * dir;
      if(avance >= atr && MathAbs(sl - op) > 0.0001)
      {
         double nuevo_sl = op + dir * atr * 0.2;  // BE + buffer pequeno
         if((dir==1 && nuevo_sl>sl) || (dir==-1 && nuevo_sl<sl))
         {
            ModificarSLTP(nuevo_sl, tp, ticket);
            Print("[BE] Ticket ", ticket, " SL movido a BE");
         }
      }

      // Trailing cuando profit >= 2x ATR
      if(avance >= 2*atr)
      {
         double nuevo_sl = sl + dir * atr * 0.8;
         if((dir==1 && nuevo_sl>sl) || (dir==-1 && nuevo_sl<sl))
            ModificarSLTP(nuevo_sl, tp, ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Modificar SL/TP de posicion                                       |
//+------------------------------------------------------------------+
void ModificarSLTP(double nuevo_sl, double tp, ulong ticket)
{
   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol = _Symbol;
   req.sl = nuevo_sl;
   req.tp = tp;
   if(!OrderSend(req, res))
      Print("[ERROR] Modificar SL/TP fallo: ", res.retcode);
}

//+------------------------------------------------------------------+
//| Cerrar todas las posiciones                                       |
//+------------------------------------------------------------------+
void CerrarTodasPosiciones(string motivo)
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      g_trade.PositionClose(ticket, 10, motivo);
   }
}

//+------------------------------------------------------------------+
//| Verificar si ya existe posicion con cierto magic                  |
//+------------------------------------------------------------------+
bool TienePosicionMagic(int magic)
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) == magic) return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Inicializar archivo CSV de trades                                 |
//+------------------------------------------------------------------+
void InicializarHistorial()
{
   int handle = FileOpen(g_historialPath, FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, "ticket,ts,bot,direccion,precio_entrada,sl,tp,lote,estado,precio_salida,pnl\n");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Registrar trade en CSV                                            |
//+------------------------------------------------------------------+
void RegistrarTrade(string bot, string dir, double precio, double sl, double tp,
                    double lote, string estado, double precio_salida=0, double pnl=0)
{
   int handle = FileOpen(g_historialPath, FILE_READ|FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle == INVALID_HANDLE)
   {
      // Si no existe, recrear
      InicializarHistorial();
      handle = FileOpen(g_historialPath, FILE_READ|FILE_WRITE|FILE_TXT|FILE_COMMON);
   }
   if(handle == INVALID_HANDLE) return;

   FileSeek(handle, 0, SEEK_END);
   string linea = StringFormat("%I64d,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
      (long)TimeCurrent(),
      TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
      bot, dir,
      DoubleToString(precio, 5),
      DoubleToString(sl, 5),
      DoubleToString(tp, 5),
      DoubleToString(lote, 2),
      estado,
      DoubleToString(precio_salida, 5),
      DoubleToString(pnl, 2));
   FileWriteString(handle, linea);
   FileClose(handle);
}

//+------------------------------------------------------------------+
//| Helper: signo                                                     |
//+------------------------------------------------------------------+
double MathSign(double v)
{
   if(v > 0) return 1.0;
   if(v < 0) return -1.0;
   return 0.0;
}
//+------------------------------------------------------------------+
