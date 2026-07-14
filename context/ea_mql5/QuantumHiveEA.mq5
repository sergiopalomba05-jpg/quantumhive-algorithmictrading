//+------------------------------------------------------------------+
//|                                    QuantumHiveEA.mq5              |
//|                        QuantumHive — Trading Algoritmico Enterprise|
//|                        Carga 3 ONNX: Madre + Hijo + Scalper       |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property link      "https://quantumhive.io"
#property version   "1.00"
#property strict

#include "FiltroHorario.mqh"
#include "GestorRiesgoEA.mqh"

input string   InpNombreBot        = "QuantumHive_US30";
input string   InpRutaMadreONNX     = "BotsCuanticos/madre.onnx";
input string   InpRutaHijoONNX      = "BotsCuanticos/reversion.onnx";  // o continuacion.onnx
input string   InpRutaScalperONNX   = "BotsCuanticos/scalper.onnx";
input bool     InpUsarCNN           = false;
input string   InpRutaCNNONNX       = "BotsCuanticos/cnn.onnx";
input double   InpRiesgoPct         = 1.0;
input double   InpRatioTP1          = 2.0;
input double   InpRatioTP2          = 4.0;
input double   InpPipsBE            = 3.0;
input bool     InpModoChallenge     = false;
input double   InpMaxDDDiario       = 4.0;
input double   InpMaxDDTotal        = 8.0;
input int      InpVentanaApertura   = 90;
input int      InpATRPeriodo       = 14;
input double   InpATRMultSL         = 1.5;
input int      InpRSIPeriodo       = 14;

// ONNX handles
long handle_madre = INVALID_HANDLE;
long handle_hijo  = INVALID_HANDLE;
long handle_scalper = INVALID_HANDLE;
long handle_cnn   = INVALID_HANDLE;

// Estado del orquestador
enum ENUM_BOT_ACTIVO { BOT_NINGUNO, BOT_REVERSION, BOT_CONTINUACION, BOT_SCALPER };
ENUM_BOT_ACTIVO bot_activo = BOT_NINGUNO;
int    ops_hoy = 0;
datetime ultimo_dia = 0;
bool   be_aplicado = false;

// Features Madre (14) normalizadas
float  obs_madre[14];
// Features Hijo (15-17)
float  obs_hijo[17];
// Features Scalper (19)
float  obs_scalper[19];

// Datos H1/H4 para Madre
datetime last_bar_h1 = 0;
datetime last_bar_h4 = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!EstaEnSesionNY())
   {
      Print("[QuantumHive] Inicializado fuera de sesión NY. Esperando...");
   }

   // Cargar ONNX Madre
   handle_madre = OnnxCreate(InpRutaMadreONNX);
   if(handle_madre == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudo cargar ONNX Madre: ", InpRutaMadreONNX, " err=", OnnxGetLastError());
      return(INIT_FAILED);
   }
   Print("[OK] ONNX Madre cargado.", InpRutaMadreONNX);

   // Cargar ONNX Hijo (reversion o continuacion)
   handle_hijo = OnnxCreate(InpRutaHijoONNX);
   if(handle_hijo == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudo cargar ONNX Hijo: ", InpRutaHijoONNX, " err=", OnnxGetLastError());
      return(INIT_FAILED);
   }
   Print("[OK] ONNX Hijo cargado.", InpRutaHijoONNX);

   // Cargar ONNX Scalper
   handle_scalper = OnnxCreate(InpRutaScalperONNX);
   if(handle_scalper == INVALID_HANDLE)
   {
      Print("[WARN] No se pudo cargar ONNX Scalper: ", InpRutaScalperONNX, " err=", OnnxGetLastError());
      // No es fatal: el scalper es opcional en modo fallback
   }
   else
      Print("[OK] ONNX Scalper cargado.", InpRutaScalperONNX);

   // CNN opcional
   if(InpUsarCNN)
   {
      handle_cnn = OnnxCreate(InpRutaCNNONNX);
      if(handle_cnn == INVALID_HANDLE)
         Print("[WARN] CNN no cargada: ", InpRutaCNNONNX);
      else
         Print("[OK] CNN cargada.", InpRutaCNNONNX);
   }

   // Inicializar gestor riesgo
   InicializarGestorRiesgo(InpModoChallenge, InpMaxDDDiario, InpMaxDDTotal);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(handle_madre != INVALID_HANDLE) OnnxRelease(handle_madre);
   if(handle_hijo != INVALID_HANDLE)  OnnxRelease(handle_hijo);
   if(handle_scalper != INVALID_HANDLE) OnnxRelease(handle_scalper);
   if(handle_cnn != INVALID_HANDLE)   OnnxRelease(handle_cnn);
   Print("[QuantumHive] ONNX liberados. Motivo: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Reset diario
   datetime hoy = TimeCurrent();
   if(TimeDay(hoy) != TimeDay(ultimo_dia))
   {
      ops_hoy = 0;
      be_aplicado = false;
      bot_activo = BOT_NINGUNO;
      ultimo_dia = hoy;
      ResetDiarioGestorRiesgo();
   }

   // Filtro horario: solo operar en sesion NY apertura
   if(!EstaEnAperturaNY(InpVentanaApertura))
   {
      if(bot_activo != BOT_NINGUNO && !PositionSelect(_Symbol))
         bot_activo = BOT_NINGUNO;
      return;
   }

   // Verificar riesgo
   if(!CuentaDentroDeRiesgo(InpModoChallenge, InpMaxDDDiario, InpMaxDDTotal))
   {
      CerrarTodasPosiciones("STOP_RIESGO");
      return;
   }

   // Gestionar posicion abierta
   if(PositionSelect(_Symbol))
   {
      GestionarPosicionAbierta();
      return;
   }

   // Max 2 ops dia (primarias) + scalper puede sumar
   if(ops_hoy >= 2 && bot_activo != BOT_SCALPER)
      return;

   // ─── FASE 1: BOT MADRE ───
   if(!CalcularObsMadre())
      return;

   long out_madre[1];
   if(!OnnxRun(handle_madre, ONNX_DEFAULT, obs_madre, out_madre))
   {
      Print("[ERROR] OnnxRun Madre fallo: ", OnnxGetLastError());
      return;
   }
   int accion_madre = (int)out_madre[0];  // 0=Reversion, 1=Continuacion, 2=Scalper

   // CNN override (opcional)
   if(InpUsarCNN && handle_cnn != INVALID_HANDLE)
   {
      // Capturar imagen del grafico y pasar por CNN (placeholder: requiere implementacion visual)
      // if(cnn_prob < 0.50) return;  // override visual bloquea
   }

   // ─── FASE 2: BOT HIJO (Reversion o Continuacion) ───
   if(accion_madre == 0 || accion_madre == 1)
   {
      if(!CalcularObsHijo())
         return;

      long out_hijo[1];
      if(!OnnxRun(handle_hijo, ONNX_DEFAULT, obs_hijo, out_hijo))
      {
         Print("[ERROR] OnnxRun Hijo fallo: ", OnnxGetLastError());
         return;
      }
      int accion_hijo = (int)out_hijo[0];  // 0=esperar, 1=comprar, 2=vender

      if(accion_hijo == 0)
         return;  // hijo decide esperar

      bot_activo = (accion_madre == 0) ? BOT_REVERSION : BOT_CONTINUACION;
      int dir = (accion_hijo == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      AbrirOperacion(dir, InpRiesgoPct, InpRatioTP1, InpRatioTP2, InpATRMultSL);
      ops_hoy++;
      return;
   }

   // ─── FASE 3: BOT SCALPER ───
   if(accion_madre == 2 && handle_scalper != INVALID_HANDLE)
   {
      if(!CalcularObsScalper())
         return;

      long out_scalper[1];
      if(!OnnxRun(handle_scalper, ONNX_DEFAULT, obs_scalper, out_scalper))
      {
         Print("[ERROR] OnnxRun Scalper fallo: ", OnnxGetLastError());
         return;
      }
      int accion_scalper = (int)out_scalper[0];  // 0=esperar, 1=comprar, 2=vender

      if(accion_scalper == 0)
         return;

      bot_activo = BOT_SCALPER;
      int dir = (accion_scalper == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      // Scalper: riesgo base 1%, TP 1:2, SL ATR*1.2
      AbrirOperacion(dir, 1.0, 2.0, 2.0, 1.2);
      return;
   }
}

//+------------------------------------------------------------------+
//| Calcular observation Madre (14 features)                         |
//+------------------------------------------------------------------+
bool CalcularObsMadre()
{
   double bbw_h1 = iATR(_Symbol, PERIOD_H1, InpATRPeriodo) / iMA(_Symbol, PERIOD_H1, 30, 0, MODE_SMA, PRICE_CLOSE);
   double bbw_h4 = iATR(_Symbol, PERIOD_H4, InpATRPeriodo) / iMA(_Symbol, PERIOD_H4, 30, 0, MODE_SMA, PRICE_CLOSE);
   double rsi_h1 = iRSI(_Symbol, PERIOD_H1, InpRSIPeriodo, PRICE_CLOSE);

   obs_madre[0] = (float)MathClamp(bbw_h1 * 20.0 - 1.0, -1.0, 1.0);
   obs_madre[1] = (float)MathClamp(bbw_h4 * 20.0 - 1.0, -1.0, 1.0);
   obs_madre[2] = (float)MathClamp((iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE) - iMA(_Symbol, PERIOD_H1, 50, 1, MODE_EMA, PRICE_CLOSE)) * 1000.0, -1.0, 1.0);
   obs_madre[3] = (float)MathClamp(rsi_h1 / 50.0 - 1.0, -1.0, 1.0);
   obs_madre[4] = 0.0f;  // estructura_h4 placeholder
   obs_madre[5] = (float)MathClamp(MathSign(iClose(_Symbol, PERIOD_D1, 0) - iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE)), -1.0, 1.0);
   obs_madre[6] = 0.0f;  // pos vs EMA200 D1 placeholder
   obs_madre[7] = 0.0f;  // dist S/R D1 placeholder
   obs_madre[8] = (float)MathClamp(MathSign(iClose(_Symbol, PERIOD_W1, 0) - iMA(_Symbol, PERIOD_W1, 50, 0, MODE_EMA, PRICE_CLOSE)), -1.0, 1.0);
   obs_madre[9] = 0.0f;  // pos vs EMA200 W1 placeholder
   obs_madre[10] = 0.0f; // dist S/R W1 placeholder
   obs_madre[11] = (float)MathClamp((bbw_h1 * 20.0 - 1.0 + (rsi_h1 / 50.0 - 1.0) * 0.5) / 3.0, -1.0, 1.0);  // score
   obs_madre[12] = (float)MathClamp((double)ops_hoy / 6.0 * 2.0 - 1.0, -1.0, 1.0);
   obs_madre[13] = 0.0f; // pnl dia placeholder
   return true;
}

//+------------------------------------------------------------------+
//| Calcular observation Hijo (simplificado)                         |
//+------------------------------------------------------------------+
bool CalcularObsHijo()
{
   double close = iClose(_Symbol, PERIOD_M15, 0);
   double bb_sup = iBands(_Symbol, PERIOD_M15, 30, 3.0, 0, PRICE_CLOSE, MODE_UPPER, 0);
   double bb_inf = iBands(_Symbol, PERIOD_M15, 30, 3.0, 0, PRICE_CLOSE, MODE_LOWER, 0);
   double bb_med = iBands(_Symbol, PERIOD_M15, 30, 3.0, 0, PRICE_CLOSE, MODE_MAIN, 0);
   double bbw = (bb_sup - bb_inf) / bb_med;
   double rsi = iRSI(_Symbol, PERIOD_M15, 7, PRICE_CLOSE);

   obs_hijo[0] = (float)MathClamp((close - bb_med) / (bb_sup - bb_inf + 1e-12) * 2.0 - 1.0, -1.0, 1.0);
   obs_hijo[1] = (float)MathClamp(bbw * 20.0 - 1.0, -1.0, 1.0);
   obs_hijo[2] = (float)MathClamp(rsi / 50.0 - 1.0, -1.0, 1.0);
   // ... (rellenar hasta 17 features según entorno real)
   for(int i = 3; i < 17; i++)
      obs_hijo[i] = 0.0f;
   return true;
}

//+------------------------------------------------------------------+
//| Calcular observation Scalper (19 features, placeholder)          |
//+------------------------------------------------------------------+
bool CalcularObsScalper()
{
   for(int i = 0; i < 19; i++)
      obs_scalper[i] = 0.0f;
   return true;
}

//+------------------------------------------------------------------+
//| Abrir operacion                                                   |
//+------------------------------------------------------------------+
void AbrirOperacion(int tipo, double riesgo_pct, double tp1_ratio, double tp2_ratio, double atr_sl_mult)
{
   double atr = iATR(_Symbol, PERIOD_M15, InpATRPeriodo);
   double price = (tipo == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                           : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int dir = (tipo == ORDER_TYPE_BUY) ? 1 : -1;
   double sl = price - dir * atr * atr_sl_mult;
   double tp1 = price + dir * atr * tp1_ratio;
   double tp2 = price + dir * atr * tp2_ratio;

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riesgo_usd = balance * riesgo_pct / 100.0;
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double sl_pips = MathAbs(price - sl) / _Point;
   double lotes = CalcularLote(riesgo_usd, sl_pips, tick_value);

   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.symbol = _Symbol;
   req.volume = lotes;
   req.type = tipo;
   req.price = price;
   req.sl = sl;
   req.tp = tp1;  // TP1 por defecto, TP2 gestionado por EA
   req.deviation = 10;
   req.magic = 123456;
   req.comment = InpNombreBot;

   if(!OrderSend(req, res))
      Print("[ERROR] OrderSend fallo: ", res.retcode);
   else
      Print("[OK] Operacion abierta: ", tipo, " lote=", lotes, " sl=", sl, " tp=", tp1);
}

//+------------------------------------------------------------------+
//| Gestionar posicion abierta                                        |
//+------------------------------------------------------------------+
void GestionarPosicionAbierta()
{
   double price = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                  ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                  : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double sl = PositionGetDouble(POSITION_SL);
   double tp = PositionGetDouble(POSITION_TP);
   double op = PositionGetDouble(POSITION_PRICE_OPEN);
   int dir = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;

   // Break-even
   if(!be_aplicado && MathAbs(price - op) >= InpPipsBE * _Point * 10.0)
   {
      ModificarSL(op + dir * 2.0 * _Point);
      be_aplicado = true;
   }

   // Scalper: trailing stop dinamico
   if(bot_activo == BOT_SCALPER)
   {
      double atr = iATR(_Symbol, PERIOD_M1, 14);
      double avance = (price - op) * dir;
      if(avance >= atr)
      {
         double nuevo_sl = sl + dir * atr * 0.8;
         if((dir == 1 && nuevo_sl > sl) || (dir == -1 && nuevo_sl < sl))
            ModificarSL(nuevo_sl);
      }
   }
}

//+------------------------------------------------------------------+
//| Modificar SL de posicion abierta                                  |
//+------------------------------------------------------------------+
void ModificarSL(double nuevo_sl)
{
   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP;
   req.symbol = _Symbol;
   req.sl = nuevo_sl;
   req.tp = PositionGetDouble(POSITION_TP);
   if(!OrderSend(req, res))
      Print("[ERROR] ModificarSL fallo: ", res.retcode);
}

//+------------------------------------------------------------------+
//| Cerrar todas las posiciones                                       |
//+------------------------------------------------------------------+
void CerrarTodasPosiciones(string motivo)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         MqlTradeRequest req = {};
         MqlTradeResult res = {};
         req.action = TRADE_ACTION_DEAL;
         req.symbol = _Symbol;
         req.volume = PositionGetDouble(POSITION_VOLUME);
         req.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
         req.price = (req.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                   : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         req.deviation = 10;
         req.magic = 123456;
         req.comment = motivo;
         OrderSend(req, res);
      }
   }
}

//+------------------------------------------------------------------+
//| MathClamp helper                                                  |
//+------------------------------------------------------------------+
double MathClamp(double v, double lo, double hi)
{
   if(v < lo) return lo;
   if(v > hi) return hi;
   return v;
}

//+------------------------------------------------------------------+
//| MathSign helper                                                   |
//+------------------------------------------------------------------+
double MathSign(double v)
{
   if(v > 0) return 1.0;
   if(v < 0) return -1.0;
   return 0.0;
}
//+------------------------------------------------------------------+
