//+------------------------------------------------------------------+
//| Include: GestorRiesgoEA.mqh                                       |
//| Gestión de riesgo reutilizable para todos los EAs del ecosistema  |
//+------------------------------------------------------------------+
#property strict

//+------------------------------------------------------------------+
//| Calcula lote según riesgo porcentual y SL en pips               |
//+------------------------------------------------------------------+
double CalcularLote(double riesgo_pct, double sl_pips, string simbolo)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(balance <= 0 || sl_pips <= 0 || riesgo_pct <= 0) return 0.0;
   double tick_size = SymbolInfoDouble(simbolo, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(simbolo, SYMBOL_TRADE_TICK_VALUE);
   double lot_step = SymbolInfoDouble(simbolo, SYMBOL_VOLUME_STEP);
   double lot_min = SymbolInfoDouble(simbolo, SYMBOL_VOLUME_MIN);
   double lot_max = SymbolInfoDouble(simbolo, SYMBOL_VOLUME_MAX);
   if(tick_value <= 0 || tick_size <= 0) return 0.0;
   double riesgo_usd = balance * riesgo_pct;
   double sl_money = sl_pips * tick_value / tick_size;
   if(sl_money <= 0) return 0.0;
   double lote = riesgo_usd / sl_money;
   lote = MathFloor(lote / lot_step) * lot_step;
   lote = MathMax(lote, lot_min);
   lote = MathMin(lote, lot_max);
   return lote;
}

//+------------------------------------------------------------------+
//| Aplica Break Even cuando precio alcanza TP1                     |
//+------------------------------------------------------------------+
void AplicarBreakEven(ulong ticket, double precio_entrada,
                       double ratio_tp1, int pips_be_extra)
{
   if(!PositionSelectByTicket(ticket)) return;
   double sl_actual = PositionGetDouble(POSITION_SL);
   double tp_actual = PositionGetDouble(POSITION_TP);
   double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
   int tipo = (int)PositionGetInteger(POSITION_TYPE);
   double tick_size = SymbolInfoDouble(PositionGetString(POSITION_SYMBOL), SYMBOL_TRADE_TICK_SIZE);
   double be_nuevo = (tipo == POSITION_TYPE_BUY)
                     ? open_price + pips_be_extra * tick_size
                     : open_price - pips_be_extra * tick_size;
   // Solo si BE mejora el SL actual (más cerca del precio o en dirección favorable)
   if((tipo == POSITION_TYPE_BUY && be_nuevo > sl_actual) ||
      (tipo == POSITION_TYPE_SELL && be_nuevo < sl_actual))
   {
      MqlTradeRequest req = {};
      MqlTradeResult res = {};
      req.action = TRADE_ACTION_SLTP;
      req.position = ticket;
      req.symbol = PositionGetString(POSITION_SYMBOL);
      req.sl = be_nuevo;
      req.tp = tp_actual;
      if(!OrderSend(req, res))
         Print("Error BE ticket ", ticket, " retcode=", res.retcode);
      else
         Print("BE aplicado ticket ", ticket, " SL=", be_nuevo);
   }
}

//+------------------------------------------------------------------+
//| Cierra parcialmente la posición (porcentaje)                    |
//+------------------------------------------------------------------+
void CerrarParcial(ulong ticket, double porcentaje)
{
   if(!PositionSelectByTicket(ticket)) return;
   double vol = PositionGetDouble(POSITION_VOLUME);
   double cierre = NormalizeDouble(vol * porcentaje / 100.0, 2);
   if(cierre <= 0 || cierre >= vol) return;
   MqlTradeRequest req = {};
   MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL;
   req.position = ticket;
   req.symbol = PositionGetString(POSITION_SYMBOL);
   req.volume = cierre;
   req.deviation = 10;
   req.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
              ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   req.type_filling = GetFillingMode(req.symbol);
   req.price = (req.type == ORDER_TYPE_SELL)
               ? SymbolInfoDouble(req.symbol, SYMBOL_BID)
               : SymbolInfoDouble(req.symbol, SYMBOL_ASK);
   if(!OrderSend(req, res))
      Print("Error cierre parcial ticket ", ticket, " retcode=", res.retcode);
   else
      Print("Cierre parcial ", porcentaje, "% ticket ", ticket);
}

//+------------------------------------------------------------------+
//| Verifica si la cuenta está dentro de límites de riesgo          |
//+------------------------------------------------------------------+
bool CuentaDentroDeRiesgo(double limite_dd_diario_pct,
                           double limite_dd_total_pct)
{
   double dd_dia = CalcularDDDiario();
   double dd_total = CalcularDDTotal();
   return (dd_dia > limite_dd_diario_pct && dd_total > limite_dd_total_pct);
}

//+------------------------------------------------------------------+
//| Calcula drawdown diario actual de la cuenta                     |
//+------------------------------------------------------------------+
double CalcularDDDiario()
{
   // Simplificado: historial de hoy no disponible directamente en OnTick
   // Se recomienda calcular desde historial de trades diarios
   double balance_ini = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(balance_ini <= 0) return 0.0;
   return (equity - balance_ini) / balance_ini * 100.0;
}

//+------------------------------------------------------------------+
//| Calcula drawdown total de la cuenta                             |
//+------------------------------------------------------------------+
double CalcularDDTotal()
{
   double balance_ini = AccountInfoDouble(ACCOUNT_BALANCE);  // Placeholder: usar balance inicio challenge
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(balance_ini <= 0) return 0.0;
   return (equity - balance_ini) / balance_ini * 100.0;
}

//+------------------------------------------------------------------+
//| Obtiene modo de llenado compatible con el broker                |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode(string simbolo)
{
   uint filling = (uint)SymbolInfoInteger(simbolo, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}
