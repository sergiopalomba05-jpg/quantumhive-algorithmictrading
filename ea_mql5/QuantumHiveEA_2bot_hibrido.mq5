//+------------------------------------------------------------------+
//| QuantumHiveEA_2bot_hibrido.mq5                                    |
//| EA Híbrido 2-Bot: Reversión + Continuación                        |
//| v3 — Coordinación, Trailing SL, BE, TP1/TP2, Scalper Trigger      |
//+------------------------------------------------------------------+
#property copyright "QuantumHive Trading Systems"
#property version   "3.00"
#property strict

#include "FiltroHorario.mqh"
#include "GestorRiesgoEA.mqh"

// ── INPUTS ──
input string   Symb = "XAUUSD";
input int      Magic_Rev   = 1001;
input int      Magic_Cont  = 1002;
input int      Magic_Scalp = 1003;

// ONNX models
input string   ONNX_Rev  = "modelos\\bot_reversion.onnx";
input string   ONNX_Cont = "modelos\\bot_continuacion.onnx";

// Risk
input double   RiesgoPct = 1.0;
input double   LoteBase  = 0.05;
input double   LoteScalp = 0.01;

// Trading params (alineados con entrenamiento)
input int      ATR_Periodo   = 14;
input double   SL_ATR_Mul    = 1.5;
input double   TP1_Ratio     = 2.0;
input double   TP2_Ratio     = 4.0;
input int      MinVentanaNY  = 90;

// Session
input int      NY_Open_Hour  = 14;   // 14:00 UTC = 09:00 ET
input int      NY_Close_Hour = 21;   // 21:00 UTC = 16:00 ET

// Kill-switch
input string   StopFile = "C:\\Users\\sergio\\BotsCuanticos\\data\\STOP.txt";

// ── GLOBALS ──
long handle_rev = INVALID_HANDLE;
long handle_cont = INVALID_HANDLE;

// Position tracking
struct PosInfo {
   ulong  ticket;
   double entry;
   double sl;
   double tp1;
   double tp2;
   double size;
   double max_fav;
   double min_fav;
   bool   be_done;
   bool   tp1_closed;
   int    type;      // ORDER_TYPE_BUY or ORDER_TYPE_SELL
   int    bars_held;
   string bot_name;
};
PosInfo pos_rev;
PosInfo pos_cont;

// Features (20 features aligned with training)
float features_rev[23];  // 20 + hour_norm + pos + size
float features_cont[23];

// Scalper trigger
bool scalper_enabled = false;
datetime last_scalp_time = 0;

// ── INIT ──
int OnInit()
{
   handle_rev = OnnxCreate(ONNX_Rev, 0);
   if(handle_rev == INVALID_HANDLE)
   {
      Print("[ERROR] No se cargó ONNX Reversión: ", ONNX_Rev);
      return INIT_FAILED;
   }

   handle_cont = OnnxCreate(ONNX_Cont, 0);
   if(handle_cont == INVALID_HANDLE)
   {
      Print("[ERROR] No se cargó ONNX Continuación: ", ONNX_Cont);
      OnnxRelease(handle_rev);
      return INIT_FAILED;
   }

   Print("[OK] QuantumHiveEA 2-Bot Híbrido v3 iniciado");
   Print("     Reversión: ", ONNX_Rev);
   Print("     Continuación: ", ONNX_Cont);
   return INIT_SUCCEEDED;
}

// ── DEINIT ──
void OnDeinit(const int reason)
{
   if(handle_rev != INVALID_HANDLE)  OnnxRelease(handle_rev);
   if(handle_cont != INVALID_HANDLE) OnnxRelease(handle_cont);
}

// ── TICK ──
void OnTick()
{
   string sym = (Symb == "") ? Symbol() : Symb;

   // 1. Kill-switch global
   if(FileIsExist(StopFile))
   {
      if(pos_rev.ticket > 0) CerrarTodo(sym, Magic_Rev);
      if(pos_cont.ticket > 0) CerrarTodo(sym, Magic_Cont);
      return;
   }

   // 2. Actualizar posiciones abiertas
   ActualizarPosicion(sym, pos_rev, Magic_Rev);
   ActualizarPosicion(sym, pos_cont, Magic_Cont);

   // 3. Gestionar trailing SL / BE / TP2
   if(pos_rev.ticket > 0) GestionarPos(sym, pos_rev, Magic_Rev);
   if(pos_cont.ticket > 0) GestionarPos(sym, pos_cont, Magic_Cont);

   // 4. Scalper trigger: si CONT en profit > 1:1 y momentum M1
   if(pos_cont.ticket > 0 && !pos_cont.tp1_closed && ProfitRatio(sym, pos_cont) >= 1.0)
   {
      scalper_enabled = true;
      if(TimeCurrent() - last_scalp_time > 300) // 5 min entre scalps
      {
         if(DetectarMomentumM1(sym))
         {
            AbrirScalper(sym, pos_cont.type);
            last_scalp_time = TimeCurrent();
         }
      }
   }
   else
      scalper_enabled = false;

   // 5. Filtro horario NY
   if(!EstaEnVentanaNY(NY_Open_Hour, NY_Close_Hour, MinVentanaNY))
      return;

   // 6. Drawdown check
   if(!CuentaDentroDeRiesgo(-4.0, -8.0))
   {
      Print("[RIESGO] Drawdown excedido. Pausando aperturas.");
      return;
   }

   // 7. Calcular features
   CalcularFeatures(sym, pos_rev, features_rev);
   CalcularFeatures(sym, pos_cont, features_cont);

   // 8. Inferencia ONNX (solo si no hay posición)
   float out_rev[5], out_cont[5];

   if(pos_rev.ticket == 0)
   {
      if(OnnxRun(handle_rev, 1, features_rev, out_rev))
      {
         int action_rev = ArgMax(out_rev, 5);
         if(action_rev != 0) // 0=WAIT
         {
            int dir = (action_rev <= 2) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
            double lot = (action_rev == 1 || action_rev == 3) ? LoteBase * 0.5 : LoteBase;
            if(pos_cont.ticket == 0 || pos_cont.type == dir) // no conflict
               AbrirPosicion(sym, dir, lot, pos_rev, Magic_Rev, "Reversión");
         }
      }
   }

   if(pos_cont.ticket == 0)
   {
      if(OnnxRun(handle_cont, 1, features_cont, out_cont))
      {
         int action_cont = ArgMax(out_cont, 5);
         if(action_cont != 0)
         {
            int dir = (action_cont <= 2) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
            double lot = (action_cont == 1 || action_cont == 3) ? LoteBase * 0.5 : LoteBase;
            if(pos_rev.ticket == 0 || pos_rev.type == dir) // no conflict
               AbrirPosicion(sym, dir, lot, pos_cont, Magic_Cont, "Continuación");
         }
      }
   }
}

// ── FUNCIONES AUXILIARES ──

void CalcularFeatures(string sym, PosInfo &pos, float &out[])
{
   // Precios
   double close = iClose(sym, PERIOD_M1, 0);
   double high  = iHigh(sym, PERIOD_M1, 0);
   double low   = iLow(sym, PERIOD_M1, 0);
   double open  = iOpen(sym, PERIOD_M1, 0);
   long   vol   = iVolume(sym, PERIOD_M1, 0);

   // ATR
   double atr = iATR(sym, PERIOD_M1, ATR_Periodo);

   // RSI(14)
   double rsi = iRSI(sym, PERIOD_M1, 14, PRICE_CLOSE);

   // EMAs
   double ema12 = iMA(sym, PERIOD_M1, 12, 0, MODE_EMA, PRICE_CLOSE);
   double ema26 = iMA(sym, PERIOD_M1, 26, 0, MODE_EMA, PRICE_CLOSE);

   // Bollinger (20, 2)
   double bb_upper = iBands(sym, PERIOD_M1, 20, 0, 2, PRICE_CLOSE, MODE_UPPER, 0);
   double bb_lower = iBands(sym, PERIOD_M1, 20, 0, 2, PRICE_CLOSE, MODE_LOWER, 0);
   double bb_mid   = iBands(sym, PERIOD_M1, 20, 0, 2, PRICE_CLOSE, MODE_MAIN, 0);

   // MACD
   double macd_main = iMACD(sym, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
   double macd_sig  = iMACD(sym, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 0);

   // Normalización (debe coincidir EXACTAMENTE con entrenamiento Python)
   int idx = 0;
   out[idx++] = (float)(close / close - 1.0);          // CLOSE (always 0, but kept for alignment)
   out[idx++] = (float)(high / close - 1.0);
   out[idx++] = (float)(low / close - 1.0);
   out[idx++] = (float)(open / close - 1.0);

   // Volume spike
   double vol_ma = 0;
   for(int i=0; i<20; i++) vol_ma += (double)iVolume(sym, PERIOD_M1, i);
   vol_ma /= 20.0;
   out[idx++] = (float)MathMin(vol / (vol_ma + 1e-9), 10.0);

   out[idx++] = (float)(rsi / 100.0);
   out[idx++] = (float)(ema12 / close - 1.0);
   out[idx++] = (float)(ema26 / close - 1.0);
   out[idx++] = (float)(bb_upper / close - 1.0);
   out[idx++] = (float)(bb_lower / close - 1.0);

   // bb_pct_b
   double bbw = bb_upper - bb_lower;
   out[idx++] = (float)((close - bb_lower) / (bbw + 1e-9));
   out[idx++] = (float)(bbw / (bb_mid + 1e-9));

   out[idx++] = (float)(atr / close);
   out[idx++] = (float)(MathMin(iADX(sym, PERIOD_M1, 14) / 100.0, 5.0));
   out[idx++] = (float)(macd_main / close);
   out[idx++] = (float)(macd_sig / close);

   // Mechas
   double body = MathAbs(close - open);
   out[idx++] = (float)(MathMin((high - MathMax(close, open)) / (body + 1e-9), 5.0));
   out[idx++] = (float)(MathMin((MathMin(close, open) - low) / (body + 1e-9), 5.0));
   out[idx++] = (float)(body / (high - low + 1e-9));

   // MACD confluence
   double macd_hist0 = macd_main - macd_sig;
   double macd_hist1 = iMACD(sym, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1)
                       - iMACD(sym, PERIOD_M1, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
   out[idx++] = (float)((macd_main > macd_sig && macd_hist0 > macd_hist1) ? 1.0 :
                        (macd_main < macd_sig && macd_hist0 < macd_hist1) ? -1.0 : 0.0);

   // NY session flag
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   out[idx++] = (float)((hour >= NY_Open_Hour && hour <= NY_Close_Hour) ? 1.0 : 0.0);

   // Posición actual + size
   out[idx++] = (float)(pos.ticket > 0 ? (pos.type == ORDER_TYPE_BUY ? 1 : -1) : 0);
   out[idx++] = (float)(pos.size);
}

void AbrirPosicion(string sym, int dir, double lot, PosInfo &pos, int magic, string bot)
{
   double price = (dir == ORDER_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_ASK)
                                          : SymbolInfoDouble(sym, SYMBOL_BID);
   double atr = iATR(sym, PERIOD_M1, ATR_Periodo);
   double sl_dist = atr * SL_ATR_Mul;
   double sl = (dir == ORDER_TYPE_BUY) ? price - sl_dist : price + sl_dist;
   double tp1 = (dir == ORDER_TYPE_BUY) ? price + sl_dist * TP1_Ratio : price - sl_dist * TP1_Ratio;
   double tp2 = (dir == ORDER_TYPE_BUY) ? price + sl_dist * TP2_Ratio : price - sl_dist * TP2_Ratio;

   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.symbol = sym;
   req.volume = lot;
   req.type = dir;
   req.price = price;
   req.sl = sl;
   req.tp = tp1;  // TP inicial = TP1, TP2 gestionado manualmente
   req.deviation = 10;
   req.magic = magic;
   req.comment = bot + " | TP1";
   req.type_filling = GetFillingMode(sym);

   if(!OrderSend(req, res))
   {
      Print("[ERROR] Abrir ", bot, ": ", res.retcode);
      return;
   }

   pos.ticket = res.order;
   pos.entry = price;
   pos.sl = sl;
   pos.tp1 = tp1;
   pos.tp2 = tp2;
   pos.size = lot;
   pos.max_fav = price;
   pos.min_fav = price;
   pos.be_done = false;
   pos.tp1_closed = false;
   pos.type = dir;
   pos.bars_held = 0;
   pos.bot_name = bot;

   Print("[TRADE] ", bot, " ", (dir == ORDER_TYPE_BUY ? "BUY" : "SELL"),
         " @ ", price, " Lote: ", lot,
         " SL: ", sl, " TP1: ", tp1, " TP2: ", tp2);
}

void GestionarPos(string sym, PosInfo &pos, int magic)
{
   if(pos.ticket == 0) return;
   if(!PositionSelectByTicket(pos.ticket)) { pos.ticket = 0; return; }

   double price = (pos.type == ORDER_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_BID)
                                               : SymbolInfoDouble(sym, SYMBOL_ASK);
   pos.bars_held++;

   // Actualizar máx/min favorables
   if(pos.type == ORDER_TYPE_BUY)
      pos.max_fav = MathMax(pos.max_fav, price);
   else
      pos.min_fav = MathMin(pos.min_fav, price);

   double atr = iATR(sym, PERIOD_M1, ATR_Periodo);

   // TP1 alcanzado → cerrar 50% + BE
   bool hit_tp1 = (pos.type == ORDER_TYPE_BUY) ? (price >= pos.tp1) : (price <= pos.tp1);
   if(hit_tp1 && !pos.tp1_closed)
   {
      // Cerrar 50%
      CerrarParcial(sym, pos.ticket, 50.0);
      pos.tp1_closed = true;

      // Mover SL a BE
      MqlTradeRequest req = {};
      MqlTradeResult res = {};
      req.action = TRADE_ACTION_SLTP;
      req.position = pos.ticket;
      req.symbol = sym;
      req.sl = pos.entry;  // BE
      req.tp = pos.tp2;    // actualizar a TP2
      OrderSend(req, res);
      pos.sl = pos.entry;
      pos.be_done = true;

      Print("[BE] ", pos.bot_name, " TP1 alcanzado. 50% cerrado. SL→BE @ ", pos.entry,
            " TP2: ", pos.tp2);
   }

   // Trailing SL después de BE
   if(pos.be_done && pos.bars_held > 10)
   {
      double trail_sl;
      if(pos.type == ORDER_TYPE_BUY)
      {
         trail_sl = pos.max_fav - atr * SL_ATR_Mul;
         if(trail_sl > pos.sl)
         {
            ModificarSL(sym, pos.ticket, trail_sl);
            pos.sl = trail_sl;
         }
      }
      else
      {
         trail_sl = pos.min_fav + atr * SL_ATR_Mul;
         if(trail_sl < pos.sl || pos.sl == 0)
         {
            ModificarSL(sym, pos.ticket, trail_sl);
            pos.sl = trail_sl;
         }
      }
   }

   // TP2 alcanzado (cierre por TP ya está en orden, pero logueamos)
   bool hit_tp2 = (pos.type == ORDER_TYPE_BUY) ? (price >= pos.tp2) : (price <= pos.tp2);
   if(hit_tp2)
   {
      Print("[TP2] ", pos.bot_name, " TP2 alcanzado. Trade completo.");
      pos.ticket = 0;
   }
}

void ActualizarPosicion(string sym, PosInfo &pos, int magic)
{
   if(pos.ticket == 0) return;

   // Verificar si la posición sigue abierta
   bool found = false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == pos.ticket)
      {
         found = true;
         break;
      }
   }
   if(!found)
      pos.ticket = 0;
}

void CerrarParcial(string sym, ulong ticket, double pct)
{
   if(!PositionSelectByTicket(ticket)) return;
   double vol = PositionGetDouble(POSITION_VOLUME);
   double cerrar = NormalizeDouble(vol * pct / 100.0, 2);
   if(cerrar <= 0) return;

   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.position = ticket;
   req.symbol = sym;
   req.volume = cerrar;
   req.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   req.price = (req.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(sym, SYMBOL_BID) : SymbolInfoDouble(sym, SYMBOL_ASK);
   req.deviation = 10;
   req.type_filling = GetFillingMode(sym);
   OrderSend(req, res);
}

void CerrarTodo(string sym, int magic)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetInteger(POSITION_MAGIC) == magic)
      {
         MqlTradeRequest req = {};
         MqlTradeResult res = {};
         req.action = TRADE_ACTION_DEAL;
         req.position = ticket;
         req.symbol = sym;
         req.volume = PositionGetDouble(POSITION_VOLUME);
         req.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
         req.price = (req.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(sym, SYMBOL_BID) : SymbolInfoDouble(sym, SYMBOL_ASK);
         req.deviation = 10;
         req.type_filling = GetFillingMode(sym);
         OrderSend(req, res);
      }
   }
}

void ModificarSL(string sym, ulong ticket, double new_sl)
{
   if(!PositionSelectByTicket(ticket)) return;
   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol = sym;
   req.sl = new_sl;
   req.tp = PositionGetDouble(POSITION_TP);
   OrderSend(req, res);
}

void AbrirScalper(string sym, int dir)
{
   double price = (dir == ORDER_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_ASK)
                                          : SymbolInfoDouble(sym, SYMBOL_BID);
   double atr = iATR(sym, PERIOD_M1, ATR_Periodo);
   double sl = (dir == ORDER_TYPE_BUY) ? price - atr : price + atr;
   double tp = (dir == ORDER_TYPE_BUY) ? price + atr * 2.0 : price - atr * 2.0;

   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.symbol = sym;
   req.volume = LoteScalp;
   req.type = dir;
   req.price = price;
   req.sl = sl;
   req.tp = tp;
   req.deviation = 10;
   req.magic = Magic_Scalp;
   req.comment = "Scalper | Momentum";
   req.type_filling = GetFillingMode(sym);
   OrderSend(req, res);

   if(res.retcode == TRADE_RETCODE_DONE)
      Print("[SCALPER] ", (dir == ORDER_TYPE_BUY ? "BUY" : "SELL"),
            " @ ", price, " Lote: ", LoteScalp, " TP: 1:2");
}

bool DetectarMomentumM1(string sym)
{
   // Momentum M1: últimas 3 barras en dirección
   double c0 = iClose(sym, PERIOD_M1, 0);
   double c1 = iClose(sym, PERIOD_M1, 1);
   double c2 = iClose(sym, PERIOD_M1, 2);
   double atr = iATR(sym, PERIOD_M1, 14);

   if(atr <= 0) return false;

   // 3 barras consecutivas en misma dirección + movimiento > 0.5 ATR
   if(c0 > c1 && c1 > c2 && (c0 - c2) > atr * 0.5)
      return true;
   if(c0 < c1 && c1 < c2 && (c2 - c0) > atr * 0.5)
      return true;

   return false;
}

double ProfitRatio(string sym, PosInfo &pos)
{
   if(pos.ticket == 0 || pos.entry == 0) return 0;
   double price = (pos.type == ORDER_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_BID)
                                               : SymbolInfoDouble(sym, SYMBOL_ASK);
   double pips = MathAbs(price - pos.entry);
   double sl_pips = MathAbs(pos.entry - pos.sl);
   if(sl_pips <= 0) return 0;
   return pips / sl_pips;
}

int ArgMax(float &arr[], int n)
{
   int best = 0;
   for(int i=1; i<n; i++)
      if(arr[i] > arr[best]) best = i;
   return best;
}

bool EstaEnVentanaNY(int open_h, int close_h, int minutos)
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int min_total = dt.hour * 60 + dt.min;
   int open_min = open_h * 60;
   int close_min = close_h * 60 + minutos;
   return (min_total >= open_min && min_total <= close_min);
}

int GetFillingMode(string sym)
{
   uint filling = (uint)SymbolInfoInteger(sym, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
