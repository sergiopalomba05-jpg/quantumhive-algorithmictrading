//+------------------------------------------------------------------+
//| GestorEnjambreDisperso.mqh                                       |
//| División 2B PropFirms — QuantumHive Algorithmic Trading          |
//| Gestiona la dispersión de señales a múltiples cuentas PropFirm    |
//| con delay aleatorio y variación de lote únicos por cuenta        |
//+------------------------------------------------------------------+

#include <Math\Stat\Math.mqh>

struct ParametrosDispersion
{
   int      direccion;        // 0 = SIN_OPERAR, 1 = COMPRA, 2 = VENTA
   double   lote_base;
   int      delay_min;        // segundos mínimos de delay
   int      delay_max;        // segundos máximos de delay
   double   variacion_pct;    // variación porcentual máxima del lote
   string   simbolo;
   double   precio_entrada;
   double   tp;
   double   sl;
};

//+------------------------------------------------------------------+
//| Genera delay aleatorio dentro del rango [delay_min, delay_max]   |
//+------------------------------------------------------------------+
int CalcularDelaySegundos(int delay_min, int delay_max)
{
   if(delay_max <= delay_min)
      return delay_min;
   return delay_min + MathRand() % (delay_max - delay_min + 1);
}

//+------------------------------------------------------------------+
//| Calcula factor de variación de lote único por cuenta              |
//+------------------------------------------------------------------+
double CalcularFactorVariacion(double variacion_pct)
{
   // Genera variación entre -variacion_pct y +variacion_pct
   int rango_entero = (int)(variacion_pct * 10000.0 * 2);
   int valor_aleatorio = MathRand() % (rango_entero + 1);
   double offset = (double)(valor_aleatorio - rango_entero / 2) / 10000.0;
   return 1.0 + offset;
}

//+------------------------------------------------------------------+
//| Abre una operación en la dirección indicada con el lote final     |
//+------------------------------------------------------------------+
bool AbrirOperacion(int direccion, double lote_final, string simbolo = "", double precio = 0.0, double tp = 0.0, double sl = 0.0)
{
   if(direccion != 1 && direccion != 2)
   {
      Print("[GESTOR_DISPERSO] Dirección inválida: ", direccion);
      return false;
   }

   string simbolo_operar = (simbolo == "" ? Symbol() : simbolo);
   ENUM_ORDER_TYPE tipo_orden = (direccion == 1 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);

   double precio_apertura = (precio > 0 ? precio : (direccion == 1 ? SymbolInfoDouble(simbolo_operar, SYMBOL_ASK) : SymbolInfoDouble(simbolo_operar, SYMBOL_BID)));
   double sl_final = sl;
   double tp_final = tp;

   // Si no se proporciona SL/TP, usa ATR implícito o defaults del EA padre
   if(sl_final <= 0)
      sl_final = (direccion == 1 ? precio_apertura - 150 * _Point : precio_apertura + 150 * _Point);
   if(tp_final <= 0)
      tp_final = (direccion == 1 ? precio_apertura + 300 * _Point : precio_apertura - 300 * _Point);

   MqlTradeRequest peticion = {};
   MqlTradeResult resultado = {};

   peticion.action       = TRADE_ACTION_DEAL;
   peticion.symbol       = simbolo_operar;
   peticion.volume       = lote_final;
   peticion.type         = tipo_orden;
   peticion.price        = precio_apertura;
   peticion.sl           = NormalizeDouble(sl_final, (int)SymbolInfoInteger(simbolo_operar, SYMBOL_DIGITS));
   peticion.tp           = NormalizeDouble(tp_final, (int)SymbolInfoInteger(simbolo_operar, SYMBOL_DIGITS));
   peticion.deviation    = 10;
   peticion.magic        = 276060001;  // Magic number base QuantumHive D2B
   peticion.comment      = "QH_D2B_Disperso";

   if(!OrderSend(peticion, resultado))
   {
      Print("[GESTOR_DISPERSO] Error abriendo operación: ", GetLastError(),
            " | Simbolo: ", simbolo_operar,
            " | Lote: ", lote_final,
            " | Dirección: ", (direccion == 1 ? "COMPRA" : "VENTA"));
      return false;
   }

   Print("[GESTOR_DISPERSO] Operación abierta | Ticket: ", resultado.order,
         " | Simbolo: ", simbolo_operar,
         " | Lote: ", lote_final,
         " | Dirección: ", (direccion == 1 ? "COMPRA" : "VENTA"));
   return true;
}

//+------------------------------------------------------------------+
//| Ejecuta una operación con delay y variación de lote dispersos      |
//+------------------------------------------------------------------+
bool EjecutarConDispersion(
   int direccion,
   double lote_base,
   int delay_min,
   int delay_max,
   double variacion_pct,
   string simbolo = "",
   double precio = 0.0,
   double tp = 0.0,
   double sl = 0.0
)
{
   int delay_seg = CalcularDelaySegundos(delay_min, delay_max);
   double factor = CalcularFactorVariacion(variacion_pct);
   double lote_final = NormalizeDouble(lote_base * factor, 2);

   // Valida lote mínimo/máximo del símbolo
   string simbolo_validar = (simbolo == "" ? Symbol() : simbolo);
   double lote_min = SymbolInfoDouble(simbolo_validar, SYMBOL_VOLUME_MIN);
   double lote_max = SymbolInfoDouble(simbolo_validar, SYMBOL_VOLUME_MAX);
   double lote_step = SymbolInfoDouble(simbolo_validar, SYMBOL_VOLUME_STEP);

   if(lote_final < lote_min)
      lote_final = lote_min;
   if(lote_final > lote_max)
      lote_final = lote_max;

   // Ajusta al step de lote
   lote_final = MathFloor(lote_final / lote_step) * lote_step;
   lote_final = NormalizeDouble(lote_final, 2);

   Print("[GESTOR_DISPERSO] Delay: ", delay_seg, "s | Factor: ", factor,
         " | Lote base: ", lote_base, " | Lote final: ", lote_final);

   Sleep(delay_seg * 1000);
   return AbrirOperacion(direccion, lote_final, simbolo, precio, tp, sl);
}

//+------------------------------------------------------------------+
//| Ejecuta dispersión a múltiples cuentas con delays únicos           |
//| por PropFirm (nunca dos cuentas de la misma firma en mismo segundo) |
//+------------------------------------------------------------------+
void EjecutarDispersionMultiple(
   int direccion,
   double lote_base,
   string simbolo = "",
   double precio = 0.0,
   double tp = 0.0,
   double sl = 0.0
)
{
   // En producción, estos datos se cargarían desde un archivo JSON
   // o se recibirían vía ZeroMQ desde el agente_dispersor.py
   // Aquí se define la estructura para integración

   Print("[GESTOR_DISPERSO] Dispersión múltiple iniciada: ",
         (direccion == 1 ? "COMPRA" : (direccion == 2 ? "VENTA" : "SIN_OPERAR")));

   // Placeholder para array de cuentas activas cargado dinámicamente
   // Ejemplo de integración con EA principal:
   // for each cuenta in cuentas_activas:
   //    EjecutarConDispersion(direccion, lote_base, cuenta.delay_min, cuenta.delay_max,
   //                          cuenta.variacion_pct, simbolo, precio, tp, sl);
}

//+------------------------------------------------------------------+
