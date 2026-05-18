//+------------------------------------------------------------------+
//| PlantillaEAHibrido.mq5                                            |
//| EA híbrido ONNX + reglas gestión riesgo                           |
//+------------------------------------------------------------------+
#property strict

#include "FiltroHorario.mqh"
#include "GestorRiesgoEA.mqh"

input string NombreBot = "BotUS30";
input string RutaONNX = "modelos_onnx\\bot_us30.onnx";
input double RiesgoPct = 1.0;
input double RatioTP1 = 2.0;
input double RatioTP2 = 4.0;
input int PipsBE = 5;
input bool ModoChallenge = true;
input double LimiteDDDiarioPct = -4.0;
input double LimiteDDTotalPct = -8.0;
input int MinutosVentanaApertura = 90;
input int ATRPeriodo = 14;
input double ATRMultiplicadorSL = 1.5;

long modelo_handle = INVALID_HANDLE;
ulong ticket_activo = 0;
double precio_entrada = 0.0;
double tp1_precio = 0.0;
double tp2_precio = 0.0;
double sl_precio = 0.0;
double lote_operacion = 0.0;
bool be_aplicado = false;
datetime hora_ultimo_cierre = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   modelo_handle = OnnxCreate(RutaONNX, 0);
   if(modelo_handle == INVALID_HANDLE)
   {
      Print("ERROR: no se pudo cargar ONNX ", RutaONNX);
      return INIT_FAILED;
   }
   Print("ONNX cargado: ", NombreBot, " handle=", modelo_handle);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(modelo_handle != INVALID_HANDLE)
      OnnxRelease(modelo_handle);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   string simbolo = Symbol();

   // 1. Verificar sesión apertura NY
   if(!EstaEnAperturaNY(MinutosVentanaApertura))
   {
      if(ticket_activo > 0) GestionarPosicionAbierta(simbolo);
      return;
   }

   // 2. Verificar riesgo
   if(!CuentaDentroDeRiesgo(LimiteDDDiarioPct, LimiteDDTotalPct))
   {
      Print("Límite DD alcanzado. Pausando EA.");
      return;
   }

   // 3. Calcular indicadores básicos
   int handle_bb = iBands(simbolo, PERIOD_M15, 30, 0, 3.0, PRICE_CLOSE);
   int handle_rsi = iRSI(simbolo, PERIOD_M15, 7, PRICE_CLOSE);
   int handle_atr = iATR(simbolo, PERIOD_M15, ATRPeriodo);
   if(handle_bb == INVALID_HANDLE || handle_rsi == INVALID_HANDLE || handle_atr == INVALID_HANDLE)
      return;
   CopyBuffer(handle_bb, 0, 0, 3, bb_main);  // Placeholder: declarar arrays
   // (En código completo se declaran arrays globales y se llenan con CopyBuffer)

   double atr_val = iATR(simbolo, PERIOD_M15, ATRPeriodo);
   if(atr_val <= 0) return;

   // 4. Preparar observación para ONNX (simplificado)
   float observacion[14];
   // ... poblar observacion con datos normalizados ...

   // 5. Inferencia ONNX
   float salida[3];
   // OnnxRun(modelo_handle, 1, observacion, salida); // Placeholder para integración real
   int accion = 0; // 0=ESPERAR, 1=LONG, 2=SHORT (ejemplo)

   // 6. Si hay posición abierta, gestionar
   if(ticket_activo > 0)
   {
      GestionarPosicionAbierta(simbolo);
      return;
   }

   // 7. Abrir operación si señal válida
   if(accion == 0) return;

   double precio = (accion == 1) ? SymbolInfoDouble(simbolo, SYMBOL_ASK)
                                 : SymbolInfoDouble(simbolo, SYMBOL_BID);
   double sl_dist = atr_val * ATRMultiplicadorSL;
   sl_precio = (accion == 1) ? precio - sl_dist : precio + sl_dist;
   tp1_precio = (accion == 1) ? precio + sl_dist * RatioTP1 : precio - sl_dist * RatioTP1;
   tp2_precio = (accion == 1) ? precio + sl_dist * RatioTP2 : precio - sl_dist * RatioTP2;
   lote_operacion = CalcularLote(RiesgoPct / 100.0, sl_dist / Point(), simbolo);
   if(lote_operacion <= 0) return;

   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.symbol = simbolo;
   req.volume = lote_operacion;
   req.type = (accion == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   req.price = precio;
   req.sl = sl_precio;
   req.tp = tp1_precio;  // TP1 como TP inicial; TP2 gestionado manualmente
   req.deviation = 10;
   req.type_filling = GetFillingMode(simbolo);
   if(!OrderSend(req, res))
   {
      Print("Error abrir orden ", res.retcode);
      return;
   }
   ticket_activo = res.order;
   precio_entrada = precio;
   be_aplicado = false;
   Print("Orden abierta ticket=", ticket_activo, " lote=", lote_operacion,
         " SL=", sl_precio, " TP1=", tp1_precio);
}

//+------------------------------------------------------------------+
//| Gestiona posición abierta: BE, cierre parcial, TP2               |
//+------------------------------------------------------------------+
void GestionarPosicionAbierta(string simbolo)
{
   if(ticket_activo == 0 || !PositionSelectByTicket(ticket_activo)) return;
   double precio_actual = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                          ? SymbolInfoDouble(simbolo, SYMBOL_BID)
                          : SymbolInfoDouble(simbolo, SYMBOL_ASK);

   // Break Even
   if(!be_aplicado)
   {
      bool alcanzo_tp1 = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                         ? (precio_actual >= tp1_precio)
                         : (precio_actual <= tp1_precio);
      if(alcanzo_tp1)
      {
         AplicarBreakEven(ticket_activo, precio_entrada, RatioTP1, PipsBE);
         CerrarParcial(ticket_activo, 50.0);
         be_aplicado = true;
         // Actualizar TP al TP2 para el resto
         MqlTradeRequest req = {};
         MqlTradeResult res = {};
         req.action = TRADE_ACTION_SLTP;
         req.position = ticket_activo;
         req.symbol = simbolo;
         req.sl = PositionGetDouble(POSITION_SL);
         req.tp = tp2_precio;
         OrderSend(req, res);
      }
   }

   // Verificar si posición cerrada
   if(!PositionSelectByTicket(ticket_activo))
   {
      ticket_activo = 0;
      be_aplicado = false;
   }
}
