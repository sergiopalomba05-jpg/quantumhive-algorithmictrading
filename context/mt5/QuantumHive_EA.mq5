//+------------------------------------------------------------------+
//|                                       QuantumHive_Unified_EA.mq5 |
//|                        QuantumHive - Hybrid RL + Mechanical Brain  |
//+------------------------------------------------------------------+
#property copyright "QuantumHive AlgoTrading"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Math\Stat\Math.mqh>

// --- ONNX Model ---
#resource "\\Files\\bot_unificado.onnx" as uchar ExtModel[]
long ExtHandle = INVALID_HANDLE;

// --- Trading Parameters ---
input group "=== SESSION ==="
input int    InpNYStartHour = 13;      // NY Session Start Hour (UTC)
input int    InpNYStartMin  = 30;      // NY Session Start Minute
input int    InpNYDuration  = 120;     // Opening Window Minutes (120 = 13:30-15:30)

input group "=== RISK MANAGEMENT ==="
input double InpRiskPct     = 1.0;     // Risk % per trade
input double InpATRSLMult   = 1.5;     // ATR SL Multiplier (REV/CONT)
input double InpATRSLScalp  = 1.2;     // ATR SL Multiplier (SCALP)
input double InpRRTP1       = 1.0;     // TP1 Risk:Reward
input double InpRRTP2       = 2.0;     // TP2 Risk:Reward
input double InpRRScalp     = 1.5;     // Scalp Risk:Reward
input double InpFracTP1     = 0.5;     // Fraction to close at TP1
input int    InpRSIPeriod   = 7;       // RSI Period
input int    InpBBPeriod    = 30;      // Bollinger Period
input double InpBBDev       = 3.0;     // Bollinger Deviation
input int    InpATRPeriod   = 14;      // ATR Period
input int    InpEMAPeriod   = 50;      // EMA Period for slope

input group "=== ONNX FEATURES ==="
input int    InpM5Shift     = 3;       // M5 confirmation lookback (bars)
input int    InpM1Shift     = 3;       // M1 confirmation lookback (bars)

// --- Internal State ---
CTrade      m_trade;
struct PositionState {
   bool      open;
   int       dir;        // 1=LONG, -1=SHORT
   string    modo;       // REV, CONT, SCALP
   double    entry;
   double    sl;
   double    tp1;
   double    tp2;
   double    lots_total;
   double    lots_remain;
   bool      be_active;
   datetime  entry_time;
   int       ops_today;
   double    pnl_today;
};
PositionState g_pos;
datetime g_last_trade_day = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(20250626);
   
   // Load ONNX
   string model_path = "bot_unificado.onnx";
   ExtHandle = OnnxCreate(model_path);
   if(ExtHandle == INVALID_HANDLE)
   {
      // Try from resource
      string tmp_path = "\\Files\\bot_unificado.onnx";
      ExtHandle = OnnxCreate(tmp_path);
      if(ExtHandle == INVALID_HANDLE)
      {
         Print("ERROR: Failed to load ONNX model. Check file in MQL5/Files/");
         return INIT_FAILED;
      }
   }
   
   // Set input shape: [batch=1, features=10]
   ulong input_shape[] = {1, 10};
   if(!OnnxSetInputShape(ExtHandle, 0, input_shape))
   {
      Print("ERROR: Failed to set ONNX input shape");
      return INIT_FAILED;
   }
   
   Print("QuantumHive EA initialized. ONNX model loaded.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(ExtHandle != INVALID_HANDLE)
      OnnxRelease(ExtHandle);
   Print("QuantumHive EA stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Manage open position (mechanical)
   if(g_pos.open)
   {
      ManagePosition();
      return;  // Don't open new while position open
   }
   
   // 2. Check NY session window
   if(!IsNYWindow())
      return;
   
   // 3. Check if already took max trades today (2)
   datetime today = TimeCurrent();
   if(TimeToString(today, TIME_DATE) != TimeToString(g_last_trade_day, TIME_DATE))
   {
      g_pos.ops_today = 0;
      g_pos.pnl_today = 0;
      g_last_trade_day = today;
   }
   if(g_pos.ops_today >= 2)
      return;
   
   // 4. Prepare features
   float features[];
   ArrayResize(features, 10);
   
   if(!PrepareFeatures(features))
   {
      Print("ERROR: Failed to prepare features");
      return;
   }
   
   // 5. ONNX Inference
   int action = ONNXInfer(features);
   if(action <= 0)  // 0 = WAIT
      return;
   
   // 6. Validate opening conditions (mechanical guard)
   string modo;
   int dir;
   ActionToModoDir(action, modo, dir);
   
   double prob = EvaluateOpeningProbability(modo, dir);
   if(prob < 0.7)  // min_probabilidad
   {
      Print("Opening REJECTED: prob=", prob, " mode=", modo, " dir=", dir);
      return;
   }
   
   // 7. Open position
   OpenPosition(modo, dir, prob);
}

//+------------------------------------------------------------------+
//| Check if within NY opening window                                |
//+------------------------------------------------------------------+
bool IsNYWindow()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   int minutes_since_midnight = dt.hour * 60 + dt.min;
   int window_start = InpNYStartHour * 60 + InpNYStartMin;
   int window_end = window_start + InpNYDuration;
   
   return (minutes_since_midnight >= window_start && minutes_since_midnight < window_end);
}

//+------------------------------------------------------------------+
//| Prepare 10 normalized features                                   |
//+------------------------------------------------------------------+
bool PrepareFeatures(float &out_features[])
{
   // Get M15 data
   double close[], open[], high[], low[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   
   if(CopyClose(_Symbol, PERIOD_M15, 0, InpBBPeriod + 10, close) < InpBBPeriod + 10) return false;
   if(CopyOpen(_Symbol, PERIOD_M15, 0, InpBBPeriod + 10, open) < InpBBPeriod + 10) return false;
   if(CopyHigh(_Symbol, PERIOD_M15, 0, InpBBPeriod + 10, high) < InpBBPeriod + 10) return false;
   if(CopyLow(_Symbol, PERIOD_M15, 0, InpBBPeriod + 10, low) < InpBBPeriod + 10) return false;
   
   double c = close[0];
   double o = open[0];
   double h = high[0];
   double l = low[0];
   
   // Feature 0: BB %B normalized [-1, 1]
   double bb_pb = BollingerPB(close, InpBBPeriod, InpBBDev);
   out_features[0] = (float)MathClamp(bb_pb * 2.0 - 1.0, -1.0, 1.0);
   
   // Feature 1: RSI normalized [-1, 1]
   double rsi = iRSI(_Symbol, PERIOD_M15, InpRSIPeriod, PRICE_CLOSE);
   out_features[1] = (float)MathClamp(rsi / 50.0 - 1.0, -1.0, 1.0);
   
   // Feature 2: BBW Estado [-1, 0, 1]
   double bbw_state = BollingerBWState(close, InpBBPeriod, InpBBDev);
   out_features[2] = (float)MathClamp(bbw_state, -1.0, 1.0);
   
   // Feature 3: EMA Slope normalized
   double ema_slope = EMASlope(close, InpEMAPeriod);
   out_features[3] = (float)MathClamp(ema_slope * 1000.0, -1.0, 1.0);
   
   // Feature 4: M5 Confirmation [0, 1]
   out_features[4] = (float)TFConfirmation(PERIOD_M5, InpM5Shift);
   
   // Feature 5: M1 Confirmation [0, 1]
   out_features[5] = (float)TFConfirmation(PERIOD_M1, InpM1Shift);
   
   // Feature 6: H1 Trend [-1, 1]
   double h1_trend = H1Trend();
   out_features[6] = (float)MathClamp(h1_trend, -1.0, 1.0);
   
   // Feature 7: ATR / Close * 100
   double atr = iATR(_Symbol, PERIOD_M15, InpATRPeriod);
   out_features[7] = (float)MathClamp(atr / c * 100.0, -1.0, 1.0);
   
   // Feature 8: Position State [-1, 0, 1]
   out_features[8] = 0.0f;  // No position open
   
   // Feature 9: Daily PnL normalized
   double pnl_norm = MathClamp(g_pos.pnl_today / AccountInfoDouble(ACCOUNT_BALANCE) * 10.0, -1.0, 1.0);
   out_features[9] = (float)pnl_norm;
   
   return true;
}

//+------------------------------------------------------------------+
//| ONNX Inference                                                   |
//+------------------------------------------------------------------+
int ONNXInfer(float &features[])
{
   // Features shape: [1, 10]
   float input_data[1][10];
   for(int i = 0; i < 10; i++)
      input_data[0][i] = features[i];
   
   // Run inference - output is logits or probabilities for 7 actions
   float output_data[1][7];
   
   if(!OnnxRun(ExtHandle, ONNX_NO_CONVERSION, input_data, output_data))
   {
      Print("ERROR: ONNX inference failed");
      return -1;
   }
   
   // Argmax to get action
   int best_action = 0;
   float best_val = output_data[0][0];
   for(int i = 1; i < 7; i++)
   {
      if(output_data[0][i] > best_val)
      {
         best_val = output_data[0][i];
         best_action = i;
      }
   }
   
   return best_action;
}

//+------------------------------------------------------------------+
//| Evaluate opening probability (mechanical guard)                  |
//+------------------------------------------------------------------+
double EvaluateOpeningProbability(string modo, int dir)
{
   double score = 0.0;
   
   double close[], high[], low[], open[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(open, true);
   CopyClose(_Symbol, PERIOD_M15, 0, 5, close);
   CopyHigh(_Symbol, PERIOD_M15, 0, 5, high);
   CopyLow(_Symbol, PERIOD_M15, 0, 5, low);
   CopyOpen(_Symbol, PERIOD_M15, 0, 5, open);
   
   double c = close[0], o = open[0], h = high[0], l = low[0];
   double sup = iBands(_Symbol, PERIOD_M15, InpBBPeriod, 0, InpBBDev, PRICE_CLOSE, MODE_UPPER, 0);
   double inf = iBands(_Symbol, PERIOD_M15, InpBBPeriod, 0, InpBBDev, PRICE_CLOSE, MODE_LOWER, 0);
   double media = iBands(_Symbol, PERIOD_M15, InpBBPeriod, 0, InpBBDev, PRICE_CLOSE, MODE_MAIN, 0);
   double rsi = iRSI(_Symbol, PERIOD_M15, InpRSIPeriod, PRICE_CLOSE);
   double bbw_state = BollingerBWState(close, InpBBPeriod, InpBBDev);
   double pend = EMASlope(close, InpEMAPeriod);
   double conf_m5 = TFConfirmation(PERIOD_M5, InpM5Shift);
   double conf_m1 = TFConfirmation(PERIOD_M1, InpM1Shift);
   double tend_h1 = H1Trend();
   
   // Momentum detection
   bool momentum_up = (c > o) && (c - o) > (h - l) * 0.3 && pend > 0;
   bool momentum_down = (c < o) && (o - c) > (h - l) * 0.3 && pend < 0;
   
   if(modo == "REV")
   {
      if(dir == 1)  // REV LONG
      {
         score += (l <= inf && c > inf) ? 0.3 : 0.0;
         score += (rsi < 35.0) ? 0.25 : MathMax(0.0, 0.25 * (50.0 - rsi) / 15.0);
         if(momentum_up) score -= 0.6;
         if(momentum_up && bbw_state > 0) score -= 0.4;
      }
      else  // REV SHORT
      {
         score += (h >= sup && c < sup) ? 0.3 : 0.0;
         score += (rsi > 65.0) ? 0.25 : MathMax(0.0, 0.25 * (rsi - 50.0) / 15.0);
         if(momentum_down) score -= 0.6;
         if(momentum_down && bbw_state > 0) score -= 0.4;
      }
      score += 0.15 * conf_m5 + 0.1 * conf_m1;
      score += (bbw_state < 0) ? 0.1 : 0.0;
   }
   else if(modo == "CONT")
   {
      if(dir == 1)  // CONT LONG
      {
         bool cuerpo = c > sup || (c - sup) / MathMax(1e-12, sup - media) > 0.2;
         score += cuerpo ? 0.25 : MathMax(0.0, (c - media) / MathMax(1e-12, sup - media)) * 0.25;
         score += (45.0 <= rsi && rsi <= 75.0) ? 0.2 : 0.1;
         score += (pend > 0 || tend_h1 >= 0) ? 0.15 : 0.0;
         if(momentum_up && conf_m5 > 0.5 && conf_m1 > 0.5) score += 0.25;
      }
      else  // CONT SHORT
      {
         bool cuerpo = c < inf || (inf - c) / MathMax(1e-12, media - inf) > 0.2;
         score += cuerpo ? 0.25 : MathMax(0.0, (media - c) / MathMax(1e-12, media - inf)) * 0.25;
         score += (25.0 <= rsi && rsi <= 55.0) ? 0.2 : 0.1;
         score += (pend < 0 || tend_h1 <= 0) ? 0.15 : 0.0;
         if(momentum_down && conf_m5 > 0.5 && conf_m1 > 0.5) score += 0.25;
      }
      score += 0.15 * conf_m5 + 0.1 * conf_m1;
      score += (bbw_state > 0) ? 0.1 : 0.0;
   }
   else if(modo == "SCALP")
   {
      score += conf_m5 ? 0.3 : 0.0;
      score += conf_m1 ? 0.3 : 0.0;
      score += (bbw_state > 0) ? 0.1 : (bbw_state == 0 ? 0.05 : 0.0);
      if(dir == 1 && momentum_up) score += 0.2;
      if(dir == -1 && momentum_down) score += 0.2;
      if(dir == 1)
      {
         score += (l <= media && media <= c) ? 0.15 : 0.0;
         score += (rsi > 40.0) ? 0.15 : 0.0;
      }
      else
      {
         score += (h >= media && media >= c) ? 0.15 : 0.0;
         score += (rsi < 60.0) ? 0.15 : 0.0;
      }
   }
   
   // Castigo contra tendencia H1 fuerte
   if(MathAbs(tend_h1) >= 0.5)
   {
      if(MathSign(dir) != MathSign(tend_h1))
      {
         if(modo == "CONT") score -= 0.4;
         else if(modo == "SCALP") score -= 0.15;
         else if(modo == "REV")
         {
            if((dir == 1 && rsi > 30.0) || (dir == -1 && rsi < 70.0))
               score -= 0.2;
         }
      }
   }
   
   return MathClamp(score, 0.0, 1.0);
}

//+------------------------------------------------------------------+
//| Open position with mechanical management                         |
//+------------------------------------------------------------------+
void OpenPosition(string modo, int dir, double prob)
{
   double price = (dir == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                             : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Calculate ATR
   double atr = iATR(_Symbol, PERIOD_M15, InpATRPeriod);
   double sl_dist = atr * ((modo == "SCALP") ? InpATRSLScalp : InpATRSLMult);
   double rr = (modo == "SCALP") ? InpRRScalp : InpRRTP2;
   
   double sl = price - dir * sl_dist;
   double tp1 = price + dir * sl_dist * InpRRTP1;
   double tp2 = price + dir * sl_dist * rr;
   
   // Calculate lots based on risk
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double sl_points = MathAbs(price - sl) / _Point;
   
   double risk_amount = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPct / 100.0;
   double lots = risk_amount / (sl_points * tick_value);
   lots = MathFloor(lots / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lots = MathMax(lots, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));
   lots = MathMin(lots, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX));
   
   ENUM_ORDER_TYPE order_type = (dir == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   if(!m_trade.PositionOpen(_Symbol, order_type, lots, price, sl, tp2))
   {
      Print("ERROR: Failed to open position. Err=", GetLastError());
      return;
   }
   
   // Save state
   g_pos.open = true;
   g_pos.dir = dir;
   g_pos.modo = modo;
   g_pos.entry = price;
   g_pos.sl = sl;
   g_pos.tp1 = tp1;
   g_pos.tp2 = tp2;
   g_pos.lots_total = lots;
   g_pos.lots_remain = lots;
   g_pos.be_active = false;
   g_pos.entry_time = TimeCurrent();
   g_pos.ops_today++;
   
   Print("OPEN ", modo, " ", (dir == 1 ? "LONG" : "SHORT"), " @", price,
         " SL=", sl, " TP1=", tp1, " TP2=", tp2, " Lots=", lots, " Prob=", prob);
}

//+------------------------------------------------------------------+
//| Manage open position mechanically                                  |
//+------------------------------------------------------------------+
void ManagePosition()
{
   if(!PositionSelect(_Symbol))
   {
      // Position closed externally
      g_pos.open = false;
      return;
   }
   
   double current_sl = PositionGetDouble(POSITION_SL);
   double current_tp = PositionGetDouble(POSITION_TP);
   double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
   double volume = PositionGetDouble(POSITION_VOLUME);
   long ticket = PositionGetInteger(POSITION_TICKET);
   
   // Check if SL hit and it's BE
   if(g_pos.be_active && MathAbs(current_sl - g_pos.entry) < _Point * 10)
   {
      // BE activated - let it run to TP2 or SL(BE)
   }
   
   // Check TP1 hit (partial close)
   if(!g_pos.be_active)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double current_price = (g_pos.dir == 1) ? bid : ask;
      
      bool tp1_hit = (g_pos.dir == 1 && bid >= g_pos.tp1) || (g_pos.dir == -1 && ask <= g_pos.tp1);
      
      if(tp1_hit)
      {
         // Close half position
         double close_lots = g_pos.lots_total * InpFracTP1;
         close_lots = MathMin(close_lots, g_pos.lots_remain);
         close_lots = MathFloor(close_lots / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         
         if(close_lots >= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN))
         {
            if(!m_trade.PositionClosePartial(ticket, close_lots))
            {
               Print("ERROR: Failed partial close at TP1. Err=", GetLastError());
            }
            else
            {
               g_pos.lots_remain -= close_lots;
               g_pos.be_active = true;
               
               // Move SL to BE
               if(!m_trade.PositionModify(ticket, g_pos.entry, current_tp))
               {
                  Print("WARN: Failed to move SL to BE. Err=", GetLastError());
               }
               
               double pnl = (g_pos.tp1 - g_pos.entry) * g_pos.dir * close_lots * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE) / _Point;
               g_pos.pnl_today += pnl;
               
               Print("TP1 HIT: Closed ", close_lots, " lots. PnL=", pnl, " SL moved to BE");
            }
         }
      }
   }
   
   // Update daily PnL
   g_pos.pnl_today += PositionGetDouble(POSITION_PROFIT);
}

//+------------------------------------------------------------------+
//| Convert action to modo and direction                             |
//+------------------------------------------------------------------+
void ActionToModoDir(int action, string &modo, int &dir)
{
   switch(action)
   {
      case 1: modo = "REV";  dir = 1;  break;  // REV LONG
      case 2: modo = "REV";  dir = -1; break;  // REV SHORT
      case 3: modo = "CONT"; dir = 1;  break;  // CONT LONG
      case 4: modo = "CONT"; dir = -1; break;  // CONT SHORT
      case 5: modo = "SCALP"; dir = 1;  break; // SCALP LONG
      case 6: modo = "SCALP"; dir = -1; break; // SCALP SHORT
      default: modo = ""; dir = 0;
   }
}

//+------------------------------------------------------------------+
//| Bollinger %B                                                     |
//+------------------------------------------------------------------+
double BollingerPB(double &close[], int period, double dev)
{
   double ma = iMAOnArray(close, 0, period, 0, MODE_SMA, 0);
   double std = iStdDevOnArray(close, 0, period, 0, MODE_SMA, 0);
   double sup = ma + dev * std;
   double inf = ma - dev * std;
   double range = sup - inf;
   if(range == 0) return 0.5;
   return (close[0] - inf) / range;
}

//+------------------------------------------------------------------+
//| Bollinger BW State (-1=contraction, 0=normal, 1=expansion)       |
//+------------------------------------------------------------------+
double BollingerBWState(double &close[], int period, double dev)
{
   double ma = iMAOnArray(close, 0, period, 0, MODE_SMA, 0);
   double std = iStdDevOnArray(close, 0, period, 0, MODE_SMA, 0);
   double sup = ma + dev * std;
   double inf = ma - dev * std;
   double bbw = (sup - inf) / MathMax(ma, 1e-12);
   
   // Calculate percentiles (simplified: compare to recent range)
   double bbw_hist[];
   ArraySetAsSeries(bbw_hist, true);
   if(CopyBuffer(iBands(_Symbol, PERIOD_M15, period, 0, dev, PRICE_CLOSE), 0, 0, 200, bbw_hist) < 200)
      return 0.0;
   
   // Simple percentile approximation
   ArraySort(bbw_hist);
   double p20 = bbw_hist[40];  // 20th percentile
   double p80 = bbw_hist[160]; // 80th percentile
   
   if(bbw < p20) return -1.0;
   if(bbw > p80) return 1.0;
   return 0.0;
}

//+------------------------------------------------------------------+
//| EMA Slope                                                        |
//+------------------------------------------------------------------+
double EMASlope(double &close[], int period)
{
   double ema1 = iMAOnArray(close, 0, period, 0, MODE_EMA, 0);
   double ema2 = iMAOnArray(close, 0, period, 0, MODE_EMA, 1);
   return ema1 - ema2;
}

//+------------------------------------------------------------------+
//| TF Confirmation (M5/M1 band touches)                             |
//+------------------------------------------------------------------+
double TFConfirmation(ENUM_TIMEFRAMES tf, int shift)
{
   double h[], l[], c[], bb_sup[], bb_inf[];
   ArraySetAsSeries(h, true);
   ArraySetAsSeries(l, true);
   ArraySetAsSeries(c, true);
   
   if(CopyHigh(_Symbol, tf, 0, shift + 1, h) < shift + 1) return 0.0;
   if(CopyLow(_Symbol, tf, 0, shift + 1, l) < shift + 1) return 0.0;
   if(CopyClose(_Symbol, tf, 0, shift + 1, c) < shift + 1) return 0.0;
   
   int bb_handle = iBands(_Symbol, tf, InpBBPeriod, 0, InpBBDev, PRICE_CLOSE);
   if(bb_handle == INVALID_HANDLE) return 0.0;
   
   CopyBuffer(bb_handle, 1, 0, shift + 1, bb_sup);  // Upper
   CopyBuffer(bb_handle, 2, 0, shift + 1, bb_inf);  // Lower
   
   for(int i = 0; i <= shift; i++)
   {
      if(l[i] <= bb_inf[i] && c[i] > bb_inf[i]) return 1.0;
      if(h[i] >= bb_sup[i] && c[i] < bb_sup[i]) return 1.0;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| H1 Trend                                                         |
//+------------------------------------------------------------------+
double H1Trend()
{
   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, PERIOD_H1, 0, 50, close) < 50) return 0.0;
   
   double ema20 = iMAOnArray(close, 0, 20, 0, MODE_EMA, 0);
   double ema50 = iMAOnArray(close, 0, 50, 0, MODE_EMA, 0);
   
   double range = (iHigh(_Symbol, PERIOD_H1, 0) - iLow(_Symbol, PERIOD_H1, 0)) * 3.0;
   if(range == 0) return 0.0;
   
   return (ema20 - ema50) / range;
}

//+------------------------------------------------------------------+
//| MathClamp helper                                                 |
//+------------------------------------------------------------------+
double MathClamp(double value, double min_val, double max_val)
{
   if(value < min_val) return min_val;
   if(value > max_val) return max_val;
   return value;
}

//+------------------------------------------------------------------+
//| MathSign helper                                                  |
//+------------------------------------------------------------------+
double MathSign(double value)
{
   if(value > 0) return 1.0;
   if(value < 0) return -1.0;
   return 0.0;
}
//+------------------------------------------------------------------+
