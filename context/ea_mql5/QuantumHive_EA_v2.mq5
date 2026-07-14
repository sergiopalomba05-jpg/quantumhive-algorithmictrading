// QuantumHive_EA_v2.mq5 — ONNX Loader para bot unificado
// Carga bot_unificado.onnx desde /MQL5/Files/
// Requiere: ONNX Runtime for MQL5 (DLL externo o libreria)

#property copyright "QuantumHive AI"
#property version   "2.0"
#property strict

#include <Trade\Trade.mqh>

input group "=== ONNX Model ==="
input string ONNX_FILE = "bot_unificado.onnx";
input int    ONNX_INPUT_FEATURES = 10;
input double LOT_SIZE = 0.01;
input double RIESGO_PCT = 0.01;
input double SL_ATR_MULT = 1.5;
input double TP_ATR_MULT = 3.0;
input int    MAX_OPS = 3;

input group "=== Filtros ==="
input int    HORA_INICIO = 14; // UTC, 14 = 10h NY
input int    HORA_FIN    = 21; // UTC, 21 = 17h NY
input bool   FILTRO_HORARIO = true;

CTrade trade;
long onnx_model = INVALID_HANDLE;
double atr_buffer[];
double rsi_buffer[];
double close_buffer[];
double open_buffer[];
double high_buffer[];
double low_buffer[];

int ops_abiertas = 0;
datetime last_bar = 0;

int OnInit() {
   trade.SetExpertMagicNumber(123456);
   
   // Cargar modelo ONNX
   string path = "Files\\" + ONNX_FILE;
   if (!FileIsExist(path)) {
      Print("[ERROR] ONNX no encontrado: ", path);
      Print("[INFO] Colocar bot_unificado.onnx en MQL5/Files/");
      return INIT_FAILED;
   }
   
   // Inicializar buffers de indicadores
   ArraySetAsSeries(atr_buffer, true);
   ArraySetAsSeries(rsi_buffer, true);
   ArraySetAsSeries(close_buffer, true);
   ArraySetAsSeries(open_buffer, true);
   ArraySetAsSeries(high_buffer, true);
   ArraySetAsSeries(low_buffer, true);
   
   Print("[OK] QuantumHive EA v2.0 iniciado. Esperando ONNX...");
   Print("[INFO] Filtro horario: ", HORA_INICIO, "-", HORA_FIN, " UTC");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   Print("[BYE] QuantumHive EA detenido. Razon: ", reason);
}

void OnTick() {
   if (FILTRO_HORARIO) {
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      if (dt.hour < HORA_INICIO || dt.hour > HORA_FIN) {
         if (ops_abiertas > 0) CerrarTodas();
         return;
      }
   }
   
   datetime curr_bar = iTime(_Symbol, PERIOD_M15, 0);
   if (curr_bar == last_bar) return;
   last_bar = curr_bar;
   
   // Cargar datos
   int bars_needed = 100;
   if (CopyClose(_Symbol, PERIOD_M15, 0, bars_needed, close_buffer) < bars_needed) return;
   if (CopyOpen(_Symbol, PERIOD_M15, 0, bars_needed, open_buffer) < bars_needed) return;
   if (CopyHigh(_Symbol, PERIOD_M15, 0, bars_needed, high_buffer) < bars_needed) return;
   if (CopyLow(_Symbol, PERIOD_M15, 0, bars_needed, low_buffer) < bars_needed) return;
   
   // Calcular indicadores simples en MQL5
   double atr = CalcularATR(14);
   double rsi = CalcularRSI(7);
   double bbw = CalcularBBW(30, 3.0);
   double pb = CalcularPB(30, 3.0);
   double ema50 = CalcularEMA(50);
   double pend = (ema50 - CalcularEMA(50, 5)) * 1000;
   
   // Features normalizadas (10 features igual que entorno Python)
   double obs[];
   ArrayResize(obs, 10);
   obs[0] = MathMin(MathMax(pb * 2 - 1, -1), 1);
   obs[1] = MathMin(MathMax(rsi / 50 - 1, -1), 1);
   obs[2] = (bbw > 0.008) ? 1.0 : ((bbw < 0.003) ? -1.0 : 0.0);
   obs[3] = MathMin(MathMax(pend, -1), 1);
   obs[4] = 0.5; // conf_m5 placeholder
   obs[5] = 0.5; // conf_m1 placeholder
   obs[6] = 0.0; // tend_h1 placeholder
   obs[7] = MathMin(MathMax(atr / close_buffer[0] * 100, -1), 1);
   obs[8] = 0.0; // pos_estado (sin posicion)
   obs[9] = 0.0; // pnl_norm
   
   // ONNX inference (placeholder — requiere DLL o API externa)
   int action = PredecirAccionONNX(obs);
   
   if (action == 0 || ops_abiertas >= MAX_OPS) return;
   
   int direccion = (action == 1 || action == 2 || action == 5) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   string modo = (action == 1 || action == 3) ? "REV" : ((action == 2 || action == 4) ? "CONT" : "SCALP");
   
   double sl_dist = atr * (SL_ATR_MULT * (modo == "SCALP" ? 0.8 : 1.0));
   double tp_dist = sl_dist * TP_ATR_MULT;
   double precio = (direccion == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                                  : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl = (direccion == ORDER_TYPE_BUY) ? precio - sl_dist : precio + sl_dist;
   double tp = (direccion == ORDER_TYPE_BUY) ? precio + tp_dist : precio - tp_dist;
   
   double riesgo = AccountInfoDouble(ACCOUNT_BALANCE) * RIESGO_PCT;
   double lote = MathFloor(riesgo / MathMax(sl_dist, 1e-12) / 100) / 100;
   lote = MathMin(MathMax(lote, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)),
                  SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX));
   lote = NormalizeDouble(lote, 2);
   
   if (direccion == ORDER_TYPE_BUY)
      trade.Buy(lote, _Symbol, 0, sl, tp, "QH_" + modo);
   else
      trade.Sell(lote, _Symbol, 0, sl, tp, "QH_" + modo);
   
   ops_abiertas++;
   Print("[TRADE] ", modo, " ", (direccion==ORDER_TYPE_BUY?"BUY":"SELL"),
         " @", precio, " SL:", sl, " TP:", tp, " Lote:", lote);
}

// Placeholder ONNX inference — requiere implementacion real
int PredecirAccionONNX(double &obs[]) {
   // TODO: Reemplazar con llamada real a ONNX Runtime
   // Por ahora: heuristica simple para demo
   if (obs[1] < -0.4 && obs[0] < -0.6) return 1; // REV LONG (RSI bajo, PB bajo)
   if (obs[1] > 0.4 && obs[0] > 0.6) return 3;   // REV SHORT (RSI alto, PB alto)
   if (obs[3] > 0.3 && obs[1] > -0.2) return 2;  // CONT LONG
   if (obs[3] < -0.3 && obs[1] < 0.2) return 4;   // CONT SHORT
   return 0;
}

void CerrarTodas() {
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong ticket = PositionGetTicket(i);
      if (ticket > 0 && PositionGetInteger(POSITION_MAGIC) == 123456)
         trade.PositionClose(ticket);
   }
   ops_abiertas = 0;
}

double CalcularATR(int periodo) {
   double tr[];
   ArraySetAsSeries(tr, true);
   int n = CopyHigh(_Symbol, PERIOD_M15, 0, periodo+1, high_buffer);
   int n2 = CopyLow(_Symbol, PERIOD_M15, 0, periodo+1, low_buffer);
   int n3 = CopyClose(_Symbol, PERIOD_M15, 0, periodo+1, close_buffer);
   if (n < 2 || n2 < 2 || n3 < 2) return 0;
   ArrayResize(tr, n);
   for (int i = 0; i < n-1; i++)
      tr[i] = MathMax(high_buffer[i] - low_buffer[i],
                      MathMax(MathAbs(high_buffer[i] - close_buffer[i+1]),
                              MathAbs(low_buffer[i] - close_buffer[i+1])));
   double atr = tr[0];
   for (int i = 1; i < MathMin(periodo, ArraySize(tr)); i++)
      atr = (atr * (periodo - 1) + tr[i]) / periodo;
   return atr;
}

double CalcularRSI(int periodo) {
   int n = CopyClose(_Symbol, PERIOD_M15, 0, periodo+2, close_buffer);
   if (n < 3) return 50;
   double gan = 0, per = 0;
   for (int i = 0; i < periodo; i++) {
      double diff = close_buffer[i] - close_buffer[i+1];
      if (diff > 0) gan += diff; else per -= diff;
   }
   double avg_g = gan / periodo;
   double avg_p = per / periodo;
   if (avg_p < 1e-12) return 100;
   return 100 - (100 / (1 + avg_g / avg_p));
}

double CalcularEMA(int periodo, int shift=0) {
   int n = CopyClose(_Symbol, PERIOD_M15, shift, periodo*2, close_buffer);
   if (n < periodo) return close_buffer[0];
   double ema = close_buffer[periodo-1];
   double mult = 2.0 / (periodo + 1);
   for (int i = periodo-2; i >= 0; i--)
      ema = close_buffer[i] * mult + ema * (1 - mult);
   return ema;
}

double CalcularBBW(int periodo, double desv) {
   int n = CopyClose(_Symbol, PERIOD_M15, 0, periodo, close_buffer);
   if (n < periodo) return 0;
   double media = 0;
   for (int i = 0; i < periodo; i++) media += close_buffer[i];
   media /= periodo;
   double var = 0;
   for (int i = 0; i < periodo; i++) var += MathPow(close_buffer[i] - media, 2);
   double std = MathSqrt(var / periodo);
   double sup = media + desv * std;
   double inf = media - desv * std;
   return (sup - inf) / media;
}

double CalcularPB(int periodo, double desv) {
   int n = CopyClose(_Symbol, PERIOD_M15, 0, periodo, close_buffer);
   if (n < periodo) return 0.5;
   double media = 0;
   for (int i = 0; i < periodo; i++) media += close_buffer[i];
   media /= periodo;
   double var = 0;
   for (int i = 0; i < periodo; i++) var += MathPow(close_buffer[i] - media, 2);
   double std = MathSqrt(var / periodo);
   double sup = media + desv * std;
   double inf = media - desv * std;
   return (close_buffer[0] - inf) / MathMax(sup - inf, 1e-12);
}
