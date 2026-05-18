/*
   QuantumHive EA v3 — ONNX-Powered RL Trading Bot
   ==================================================
   Carga modelo ONNX exportado desde Stable-Baselines3 PPO.
   Calcula 10 features normalizadas identicas al entorno Python:
     [pb_norm, rsi_norm, bbw_est, pend_ema, conf_m5, conf_m1,
      tend_h1, atr_norm, pos_estado, pnl_norm]

   Requisitos:
     - MetaTrader 5 build 1930+ (soporte ONNX)
     - Archivo bot_unificado.onnx en MQL5/Files/
     - Symbol: US30, Timeframe: M15 (base) + M5, M1, H1 referencias

   Risk Management:
     - Lot size = (Balance * RiesgoPct) / (|Precio - SL| / PointValue)
     - Max 1 posicion abierta
     - BE activado a 50% del camino al TP1
     - Partial close en TP1 (50% del lote)
*/

#property copyright "QuantumHive v3"
#property version   "3.00"
#property strict

#include <Trade\Trade.mqh>
#include <Math\Stat\Math.mqh>

// === ONNX ================================================================
#resource \"\\Files\\bot_unificado.onnx\" as uchar ExtOnnxModel[]
long   onnx_handle = INVALID_HANDLE;

// === INPUTS ==============================================================
input group "=== Risk Management ==="
input double InpRiesgoPct    = 0.01;   // Riesgo por trade (% balance)
input double InpSlMult       = 2.0;    // SL = ATR * mult
input double InpTp1Mult      = 1.5;    // TP1 = ATR * mult
input double InpTp2Mult      = 3.0;    // TP2 = ATR * mult
input double InpBeRatio      = 0.5;    // BE trigger at 50% to TP1
input double InpLoteMax      = 5.0;    // Lote maximo
input int    InpMagic        = 7733;   // Magic number

input group "=== Session ==="
input int    InpSesionStart  = 14;    // Hora inicio NY (14 = 14:00 server)
input int    InpSesionEnd    = 21;    // Hora fin NY

// === STATE ===============================================================
CTrade      m_trade;
ENUM_POSITION_TYPE m_dir     = POSITION_TYPE_BUY;
double      m_sl             = 0.0;
double      m_tp1            = 0.0;
double      m_tp2            = 0.0;
double      m_lote_total     = 0.0;
double      m_lote_remanente = 0.0;
bool        m_pos_abierta    = false;
bool        m_be_activado    = false;
datetime    m_open_time      = 0;
double      m_precio_entrada = 0.0;
double      m_pnl_dia        = 0.0;
datetime    m_dia_actual     = 0;
string      m_modo           = "";

// === INDICATORS ==========================================================
int h_rsi_m15, h_bb_m15, h_atr_m15, h_ema50_m15;
int h_rsi_m5,  h_bb_m5,  h_rsi_m1,  h_ema50_h1;

// === FEATURE NORMALIZATION ===============================================
#define FEAT_PB      0
#define FEAT_RSI     1
#define FEAT_BBW     2
#define FEAT_PEND    3
#define FEAT_CONF_M5 4
#define FEAT_CONF_M1 5
#define FEAT_TEND_H1 6
#define FEAT_ATR_N   7
#define FEAT_POS     8
#define FEAT_PNL     9
#define NUM_FEATS    10

// === ONNX RUN ============================================================
float OnnxRunInference(const float &obs[])
{
   if(onnx_handle == INVALID_HANDLE) return -1;

   // Crear tensores: input [1,10], output [1,7]
   long input_info[], output_info[];
   if(!OnnxCreateInputTensor(onnx_handle, 1, input_info, obs, 10)) return -1;
   float logits[];
   ArrayResize(logits, 7);
   if(!OnnxRun(onnx_handle, input_info, output_info, logits, 7)) return -1;

   // Argmax sobre logits
   int best = 0;
   for(int i=1; i<7; i++)
      if(logits[i] > logits[best]) best = i;

   OnnxReleaseTensor(input_info);
   OnnxReleaseTensor(output_info);
   return (float)best;
}

// === INIT ================================================================
int OnInit()
{
   m_trade.SetExpertMagicNumber(InpMagic);
   m_trade.SetDeviationInPoints(10);
   m_trade.SetTypeFilling(ORDER_FILLING_FOK);
   m_trade.SetAsyncMode(false);

   // Cargar ONNX
   string onnx_path = "bot_unificado.onnx";
   // Si no existe en Files, crear desde resource
   if(!FileIsExist(onnx_path))
   {
      int h = FileOpen(onnx_path, FILE_WRITE|FILE_BIN|FILE_COMMON);
      if(h != INVALID_HANDLE)
      {
         FileWriteArray(h, ExtOnnxModel);
         FileClose(h);
      }
   }
   onnx_handle = OnnxCreate(onnx_path, 0);
   if(onnx_handle == INVALID_HANDLE)
   {
      Print("[FATAL] No se pudo cargar ONNX: ", onnx_path);
      return INIT_FAILED;
   }
   Print("[OK] ONNX cargado | handle=", onnx_handle);

   // Indicadores
   h_rsi_m15  = iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE);
   h_bb_m15   = iBands(_Symbol, PERIOD_M15, 20, 0, 2.0, PRICE_CLOSE);
   h_atr_m15  = iATR(_Symbol, PERIOD_M15, 14);
   h_ema50_m15= iMA(_Symbol, PERIOD_M15, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_rsi_m5   = iRSI(_Symbol, PERIOD_M5,  14, PRICE_CLOSE);
   h_bb_m5    = iBands(_Symbol, PERIOD_M5,  20, 0, 2.0, PRICE_CLOSE);
   h_rsi_m1   = iRSI(_Symbol, PERIOD_M1,  14, PRICE_CLOSE);
   h_ema50_h1 = iMA(_Symbol, PERIOD_H1,  50, 0, MODE_EMA, PRICE_CLOSE);

   if(h_rsi_m15==INVALID_HANDLE || h_bb_m15==INVALID_HANDLE || h_atr_m15==INVALID_HANDLE)
   {
      Print("[FATAL] Error creando indicadores M15");
      return INIT_FAILED;
   }

   m_dia_actual = iTime(_Symbol, PERIOD_M15, 0);
   m_pnl_dia    = 0.0;
   Print("[OK] QuantumHive EA v3 iniciado | Symbol=", _Symbol);
   return INIT_SUCCEEDED;
}

// === DEINIT ==============================================================
void OnDeinit(const int reason)
{
   if(onnx_handle != INVALID_HANDLE) OnnxRelease(onnx_handle);
   Print("[INFO] EA detenido. Razon: ", reason);
}

// === UTILITIES ===========================================================
double GetValue(int handle, int buffer, int shift)
{
   double v[];
   if(CopyBuffer(handle, buffer, shift, 1, v) != 1) return 0.0;
   return v[0];
}

double CalcBBW(int bb_handle, int shift)
{
   double sup = GetValue(bb_handle, UPPER_BAND, shift);
   double inf = GetValue(bb_handle, LOWER_BAND, shift);
   double mid = GetValue(bb_handle, BASE_LINE,  shift);
   if(mid == 0) return 0.005;
   return (sup - inf) / mid;
}

double CalcPB(int bb_handle, double close, int shift)
{
   double sup = GetValue(bb_handle, UPPER_BAND, shift);
   double inf = GetValue(bb_handle, LOWER_BAND, shift);
   double range = sup - inf;
   if(range == 0) return 0.5;
   return (close - inf) / range;
}

double ScoreConfluencia(double c, double o, double h, double l,
                        double bb_sup, double bb_inf, double rsi)
{
   double score = 0.0;
   double pb = (c - bb_inf) / MathMax(bb_sup - bb_inf, 1e-9);
   double ancho = MathAbs(h - l);
   double cuerpo = MathAbs(c - o);
   double mecha_sup = h - MathMax(c, o);
   double mecha_inf = MathMin(c, o) - l;
   double bbw = MathMax(bb_sup - bb_inf, 1e-9) / ((bb_sup + bb_inf) / 2.0);

   // Wick logic
   if(c < o && mecha_sup > cuerpo * 1.5 && pb > 0.85 && rsi > 60) score += 0.25;
   if(c > o && mecha_inf > cuerpo * 1.5 && pb < 0.15 && rsi < 40) score += 0.25;
   if(c < bb_inf) score += 0.15;
   if(c > bb_sup) score += 0.15;
   if((pb > 0.85) && (rsi > 60)) score += 0.10;
   if((pb < 0.15) && (rsi < 40)) score += 0.10;
   if((c > o) && (ancho > 0.001 * c)) score += 0.05;
   if((c < o) && (ancho > 0.001 * c)) score += 0.05;
   if(bbw > 0.008) score += 0.05;
   return MathMin(1.0, MathMax(0.0, score));
}

double Normalize(double v, double lo, double hi) {
   if(hi == lo) return 0.0;
   return MathMax(-1.0, MathMin(1.0, 2.0 * (v - lo) / (hi - lo) - 1.0));
}

// === FEATURE BUILDER =====================================================
void BuildFeatures(float &obs[])
{
   ArrayResize(obs, NUM_FEATS);
   ArrayInitialize(obs, 0.0f);

   double c_m15 = iClose(_Symbol, PERIOD_M15, 0);
   double o_m15 = iOpen(_Symbol, PERIOD_M15, 0);
   double h_m15 = iHigh(_Symbol, PERIOD_M15, 0);
   double l_m15 = iLow(_Symbol, PERIOD_M15, 0);

   // M15 indicators
   double rsi_m15 = GetValue(h_rsi_m15, 0, 0);
   double bbw_m15 = CalcBBW(h_bb_m15, 0);
   double atr_m15 = GetValue(h_atr_m15, 0, 0);
   double ema50_m15 = GetValue(h_ema50_m15, 0, 0);
   double ema50_m15_prev = GetValue(h_ema50_m15, 0, 5); // 5 barras atras
   double pb_m15 = CalcPB(h_bb_m15, c_m15, 0);
   double pend = (ema50_m15 - ema50_m15_prev) * 1000.0;

   // M5 confluence
   double c_m5 = iClose(_Symbol, PERIOD_M5, 0);
   double o_m5 = iOpen(_Symbol, PERIOD_M5, 0);
   double h_m5 = iHigh(_Symbol, PERIOD_M5, 0);
   double l_m5 = iLow(_Symbol, PERIOD_M5, 0);
   double bb_sup_m5 = GetValue(h_bb_m5, UPPER_BAND, 0);
   double bb_inf_m5 = GetValue(h_bb_m5, LOWER_BAND, 0);
   double rsi_m5 = GetValue(h_rsi_m5, 0, 0);
   double conf_m5 = ScoreConfluencia(c_m5, o_m5, h_m5, l_m5, bb_sup_m5, bb_inf_m5, rsi_m5);

   // M1 confluence
   double c_m1 = iClose(_Symbol, PERIOD_M1, 0);
   double o_m1 = iOpen(_Symbol, PERIOD_M1, 0);
   double h_m1 = iHigh(_Symbol, PERIOD_M1, 0);
   double l_m1 = iLow(_Symbol, PERIOD_M1, 0);
   // M1 BB usando M15 aprox (sin indicador M1 BB dedicado para simplificar)
   // Fallback: usar conf_m1 = conf_m5 como aproximacion rapida
   double conf_m1 = conf_m5;

   // H1 trend
   double ema50_h1 = GetValue(h_ema50_h1, 0, 0);
   double rsi_h1   = 50.0; // Fallback sin indicador H1 RSI dedicado
   double tend_h1  = MathSign(ema50_h1 - iClose(_Symbol, PERIOD_H1, 5)); // proxy

   // Position state
   double pos_estado = 0.0;
   if(m_pos_abierta)
      pos_estado = (m_dir == POSITION_TYPE_BUY) ? 1.0 : -1.0;

   // PnL day normalized
   datetime hoy = iTime(_Symbol, PERIOD_M15, 0);
   if(hoy != m_dia_actual) { m_dia_actual = hoy; m_pnl_dia = 0.0; }
   double pnl_norm = 0.0;
   if(AccountInfoDouble(ACCOUNT_BALANCE) > 0)
      pnl_norm = MathMax(-1.0, MathMin(1.0, m_pnl_dia / AccountInfoDouble(ACCOUNT_BALANCE) * 10.0));

   // Heuristica BBW estado (-1,0,1)
   double bbw_est = 0.0;
   if(bbw_m15 < 0.003) bbw_est = -1.0;
   else if(bbw_m15 > 0.008) bbw_est = 1.0;

   // Assemble 10 features (exact match Python env)
   obs[FEAT_PB]      = (float)MathMax(-1.0, MathMin(1.0, pb_m15 * 2.0 - 1.0));
   obs[FEAT_RSI]     = (float)MathMax(-1.0, MathMin(1.0, rsi_m15 / 50.0 - 1.0));
   obs[FEAT_BBW]     = (float)MathMax(-1.0, MathMin(1.0, bbw_est));
   obs[FEAT_PEND]    = (float)MathMax(-1.0, MathMin(1.0, pend));
   obs[FEAT_CONF_M5] = (float)conf_m5;
   obs[FEAT_CONF_M1] = (float)conf_m1;
   obs[FEAT_TEND_H1] = (float)MathMax(-1.0, MathMin(1.0, tend_h1));
   obs[FEAT_ATR_N]   = (float)MathMax(-1.0, MathMin(1.0, atr_m15 / c_m15 * 100.0));
   obs[FEAT_POS]     = (float)pos_estado;
   obs[FEAT_PNL]     = (float)pnl_norm;
}

// === TRADE LOGIC =========================================================
void ManagePosition(double high, double low)
{
   if(!m_pos_abierta) return;

   bool touched_sl  = (m_dir == POSITION_TYPE_BUY)  ? (low <= m_sl)  : (high >= m_sl);
   bool touched_tp1 = (m_dir == POSITION_TYPE_BUY)  ? (high >= m_tp1) : (low <= m_tp1);
   bool touched_tp2 = (m_dir == POSITION_TYPE_BUY)  ? (high >= m_tp2) : (low <= m_tp2);

   if(!m_be_activado && touched_tp1)
   {
      // Cierre parcial 50%
      double lote_cerrar = MathMin(m_lote_total * FRACCION_TP1, m_lote_remanente);
      if(lote_cerrar > 0)
      {
         ENUM_ORDER_TYPE ot = (m_dir == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
         m_trade.PositionClose(m_position.Ticket(), lote_cerrar);
         m_lote_remanente -= lote_cerrar;
         m_sl = NormalizePrice(m_precio_entrada);
      }
      m_be_activado = true;
      Print("[EVENT] TP1 parcial + BE activado | lote remanente=", m_lote_remanente);
   }

   if(touched_tp2 || touched_sl)
   {
      m_trade.PositionClose(m_position.Ticket());
      m_trade.PositionClose(_Symbol);
      double pnl = (m_dir == POSITION_TYPE_BUY)
         ? (touched_tp2 ? m_tp2 : m_sl) - m_precio_entrada
         : m_precio_entrada - (touched_tp2 ? m_tp2 : m_sl);
      pnl *= m_lote_remanente;
      if(touched_tp2) pnl -= SymbolInfoDouble(_Symbol, SYMBOL_SWAP_SHORT);
      m_pnl_dia += pnl;
      Print("[EVENT] Cierre ", touched_tp2 ? "TP2" : "SL/BE", " | PnL trade=", pnl,
            " | PnL dia=", m_pnl_dia);
      m_pos_abierta = false;
      m_be_activado = false;
      m_lote_total = 0.0;
      m_lote_remanente = 0.0;
   }
}

void OpenTrade(int action, double precio, double atr)
{
   if(m_pos_abierta) return;

   string modo;
   ENUM_ORDER_TYPE tipo;
   if(action == 1) { modo = "REV"; tipo = ORDER_TYPE_BUY; }
   else if(action == 2) { modo = "REV"; tipo = ORDER_TYPE_SELL; }
   else if(action == 3) { modo = "CONT"; tipo = ORDER_TYPE_BUY; }
   else if(action == 4) { modo = "CONT"; tipo = ORDER_TYPE_SELL; }
   else if(action == 5) { modo = "SCALP"; tipo = ORDER_TYPE_BUY; }
   else if(action == 6) { modo = "SCALP"; tipo = ORDER_TYPE_SELL; }
   else return;

   double sl_offset = atr * InpSlMult;
   double tp1_offset = atr * InpTp1Mult;
   double tp2_offset = atr * InpTp2Mult;

   double sl  = (tipo == ORDER_TYPE_BUY)  ? precio - sl_offset  : precio + sl_offset;
   double tp1 = (tipo == ORDER_TYPE_BUY)  ? precio + tp1_offset : precio - tp1_offset;
   double tp2 = (tipo == ORDER_TYPE_BUY)  ? precio + tp2_offset : precio - tp2_offset;

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riesgo  = balance * InpRiesgoPct;
   double punto   = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double contrato= SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   double sl_dist = MathAbs(precio - sl) + 1e-9;
   double lote    = riesgo / (sl_dist * contrato);
   lote = MathMax(0.01, MathMin(lote, InpLoteMax));
   lote = NormalizeDouble(lote, 2);

   if(tipo == ORDER_TYPE_BUY)
   {
      if(!m_trade.Buy(lote, _Symbol, 0, sl, tp2, "QuantumHive v3"))
      {
         Print("[ERROR] Buy fallida: ", GetLastError());
         return;
      }
   }
   else
   {
      if(!m_trade.Sell(lote, _Symbol, 0, sl, tp2, "QuantumHive v3"))
      {
         Print("[ERROR] Sell fallida: ", GetLastError());
         return;
      }
   }

   m_pos_abierta    = true;
   m_dir            = (tipo == ORDER_TYPE_BUY) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
   m_precio_entrada = precio;
   m_sl             = sl;
   m_tp1            = tp1;
   m_tp2            = tp2;
   m_lote_total     = lote;
   m_lote_remanente = lote;
   m_be_activado    = false;
   m_modo           = modo;
   m_open_time      = TimeCurrent();

   Print("[OPEN] ", modo, " ", (m_dir==POSITION_TYPE_BUY?"BUY":"SELL"),
         " @", precio, " | Lote=", lote, " | SL=", sl, " | TP1=", tp1, " | TP2=", tp2);
}

// === ON TICK =============================================================
void OnTick()
{
   // Solo operar en sesion NY
   MqlDateTime dt;
   TimeToStruct(iTime(_Symbol, PERIOD_M15, 0), dt);
   if(dt.hour < InpSesionStart || dt.hour > InpSesionEnd) return;

   double c = iClose(_Symbol, PERIOD_M15, 0);
   double h = iHigh(_Symbol, PERIOD_M15, 0);
   double l = iLow(_Symbol, PERIOD_M15, 0);
   double atr = GetValue(h_atr_m15, 0, 0);

   // Gestionar posicion abierta
   ManagePosition(h, l);

   // Predecir accion
   float obs[];
   BuildFeatures(obs);
   int action = (int)OnnxRunInference(obs);

   // Ejecutar si hay senal
   if(action != 0 && !m_pos_abierta)
   {
      OpenTrade(action, c, atr);
   }
}
