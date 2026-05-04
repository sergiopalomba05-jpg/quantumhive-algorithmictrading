//+------------------------------------------------------------------+
//|                                                 NY PREDATOR v1.mq5 |
//|                                    QuantumHive Algorithmic Trading |
//|                                                                  |
//| Bot especialista US30 (Apertura NY)                               |
//| Selector de Modos usando ONNX                                     |
//+------------------------------------------------------------------+
#property copyright "QuantumHive"
#property link      "https://quantumhive.ai"
#property version   "1.00"
#property strict

//--- Input Parameters
input double   LotSize = 0.1;           // Tamaño del lote
input int      BB_Period = 30;         // Período Bollinger Bands
input double   BB_Dev = 3.0;           // Desviación Bollinger Bands
input int      RSI_Period = 7;         // Período RSI
input int      ATR_Period = 14;        // Período ATR
input double   ATR_SL_Mult = 2.0;      // Multiplicador ATR para SL
input double   ATR_TP_Mult = 3.0;      // Multiplicador ATR para TP
input int      MaxOpsDia = 4;          // Máximo operaciones por día
input int      MagicNumber = 10001;    // Magic Number

//--- Global Variables
double BB_Upper[], BB_Middle[], BB_Lower[];
double RSI[];
double ATR[];
double Volume_MA[];
double BB_Width[];
int ops_hoy = 0;
int ultima_dia = 0;
long onnx_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    // Inicializar arrays de indicadores
    ArraySetAsSeries(BB_Upper, true);
    ArraySetAsSeries(BB_Middle, true);
    ArraySetAsSeries(BB_Lower, true);
    ArraySetAsSeries(RSI, true);
    ArraySetAsSeries(ATR, true);
    ArraySetAsSeries(Volume_MA, true);
    ArraySetAsSeries(BB_Width, true);
    
    // Configurar manejadores de indicadores
    int bb_handle = iBands(_Symbol, PERIOD_M15, BB_Period, 0, BB_Dev, PRICE_CLOSE);
    int rsi_handle = iRSI(_Symbol, PERIOD_M15, RSI_Period, PRICE_CLOSE);
    int atr_handle = iATR(_Symbol, PERIOD_M15, ATR_Period);
    
    if(bb_handle == INVALID_HANDLE || rsi_handle == INVALID_HANDLE || atr_handle == INVALID_HANDLE)
    {
        Print("Error inicializando indicadores");
        return INIT_FAILED;
    }
    
    // Cargar modelo ONNX
    string onnx_path = "MQL5\\Files\\ny_predator_v1.onnx";
    onnx_handle = OnnxCreate(onnx_path, ONNX_DEFAULT);
    
    if(onnx_handle == INVALID_HANDLE)
    {
        Print("Error cargando modelo ONNX: ", GetLastError());
        Print("Ruta del archivo: ", onnx_path);
        return INIT_FAILED;
    }
    
    Print("NY PREDATOR v1 inicializado correctamente");
    Print("Modelo ONNX cargado exitosamente");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Liberar modelo ONNX
    if(onnx_handle != INVALID_HANDLE)
    {
        OnnxRelease(onnx_handle);
        Print("Modelo ONNX liberado");
    }
    
    Print("NY PREDATOR v1 desinicializado");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Resetear contador de operaciones al día
    MqlDateTime dt;
    TimeCurrent(dt);
    if(dt.day != ultima_dia)
    {
        ops_hoy = 0;
        ultima_dia = dt.day;
    }
    
    // Verificar máximo de operaciones
    if(ops_hoy >= MaxOpsDia) return;
    
    // Obtener datos de indicadores
    if(!ActualizarIndicadores()) return;
    
    // Detectar modo de operación
    int modo = DetectarModo();
    
    if(modo == 0)  // MODO A (Reversión)
    {
        EjecutarModoA();
    }
    else if(modo == 1)  // MODO B (Continuidad)
    {
        EjecutarModoB();
    }
}

//+------------------------------------------------------------------+
//| Actualizar indicadores técnicos                                   |
//+------------------------------------------------------------------+
bool ActualizarIndicadores()
{
    // Copiar datos de Bollinger Bands (copiar 2 elementos para poder acceder a índice 1)
    if(CopyBuffer(iBands(_Symbol, PERIOD_M15, BB_Period, 0, BB_Dev, PRICE_CLOSE), 0, 0, 2, BB_Upper) < 0) return false;
    if(CopyBuffer(iBands(_Symbol, PERIOD_M15, BB_Period, 0, BB_Dev, PRICE_CLOSE), 1, 0, 2, BB_Middle) < 0) return false;
    if(CopyBuffer(iBands(_Symbol, PERIOD_M15, BB_Period, 0, BB_Dev, PRICE_CLOSE), 2, 0, 2, BB_Lower) < 0) return false;
    
    // Copiar datos de RSI
    if(CopyBuffer(iRSI(_Symbol, PERIOD_M15, RSI_Period, PRICE_CLOSE), 0, 0, 2, RSI) < 0) return false;
    
    // Copiar datos de ATR
    if(CopyBuffer(iATR(_Symbol, PERIOD_M15, ATR_Period), 0, 0, 2, ATR) < 0) return false;
    
    // Calcular volumen promedio
    long tick_volume_array[];
    ArraySetAsSeries(tick_volume_array, true);
    if(CopyTickVolume(_Symbol, PERIOD_M15, 0, 20, tick_volume_array) < 0) return false;
    double vol_ma = 0;
    for(int i = 0; i < 20; i++) vol_ma += (double)tick_volume_array[i];
    Volume_MA[0] = vol_ma / 20;
    
    // Calcular ancho de BB
    BB_Width[0] = (BB_Upper[0] - BB_Lower[0]) / BB_Middle[0];
    
    return true;
}

//+------------------------------------------------------------------+
//| Detectar modo de operación                                        |
//+------------------------------------------------------------------+
int DetectarModo()
{
    double close = iClose(_Symbol, PERIOD_M15, 0);
    double open = iOpen(_Symbol, PERIOD_M15, 0);
    double high = iHigh(_Symbol, PERIOD_M15, 0);
    double low = iLow(_Symbol, PERIOD_M15, 0);
    double volume = iVolume(_Symbol, PERIOD_M15, 0);
    
    // MODO A (Reversión): Mecha fuera de Banda con cierre dentro y volumen de rechazo
    bool mecha_superior = high > BB_Upper[0];
    bool cierre_dentro = close < BB_Upper[0] && close > BB_Lower[0];
    bool volumen_rechazo = volume > Volume_MA[0];
    
    if(mecha_superior && cierre_dentro && volumen_rechazo)
    {
        return 0;  // MODO A
    }
    
    // MODO B (Continuidad): Cierre sólido fuera de Banda con expansión de BBW y volumen creciente
    bool cierre_fuera = close > BB_Upper[0];
    double bbw_anterior = (BB_Upper[1] - BB_Lower[1]) / BB_Middle[1];
    bool bbw_expansion = BB_Width[0] > bbw_anterior;
    double volume_anterior = iVolume(_Symbol, PERIOD_M15, 1);
    bool volumen_creciente = volume > volume_anterior;
    
    if(cierre_fuera && bbw_expansion && volumen_creciente)
    {
        return 1;  // MODO B
    }
    
    return 2;  // NO TRADE
}

//+------------------------------------------------------------------+
//| Ejecutar MODO A (Reversión) - 3 posiciones                      |
//+------------------------------------------------------------------+
void EjecutarModoA()
{
    if(PositionsTotal() > 0) return;  // Ya hay posición abierta
    
    double close = iClose(_Symbol, PERIOD_M15, 0);
    double sl = close - (ATR[0] * ATR_SL_Mult);
    double tp1 = close + (ATR[0] * ATR_TP_Mult);
    double tp2 = close + (ATR[0] * ATR_TP_Mult * 3);
    
    // Posición 1: Ratio 1:1
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = LotSize;
    request.type = ORDER_TYPE_SELL;  // Short para reversión
    request.price = close;
    request.sl = sl;
    request.tp = tp1;
    request.deviation = 10;
    request.magic = MagicNumber;
    request.comment = "NY_Predator_v1_ModoA_Pos1";
    
    if(!OrderSend(request, result))
    {
        Print("Error abriendo posición 1 MODO A: ", GetLastError());
        return;
    }
    
    ops_hoy++;
    
    // Posición 2: Ratio 1:3 (A 1:2, mover SL al nivel de la Posición 1)
    request.tp = tp2;
    request.comment = "NY_Predator_v1_ModoA_Pos2";
    
    if(!OrderSend(request, result))
    {
        Print("Error abriendo posición 2 MODO A: ", GetLastError());
        return;
    }
    
    ops_hoy++;
    
    // Posición 3: Activar solo si la vela siguiente al rechazo es un Doji
    // Esto se verificará en la siguiente vela
}

//+------------------------------------------------------------------+
//| Ejecutar MODO B (Continuidad) - 2 posiciones                    |
//+------------------------------------------------------------------+
void EjecutarModoB()
{
    if(PositionsTotal() > 0) return;  // Ya hay posición abierta
    
    double close = iClose(_Symbol, PERIOD_M15, 0);
    double sl = close - (ATR[0] * ATR_SL_Mult);
    double tp1 = close + (ATR[0] * ATR_TP_Mult);
    double tp2 = close + (ATR[0] * ATR_TP_Mult * 3);
    
    // Posición 1: Ratio 1:1
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = LotSize;
    request.type = ORDER_TYPE_BUY;  // Long para continuidad
    request.price = close;
    request.sl = sl;
    request.tp = tp1;
    request.deviation = 10;
    request.magic = MagicNumber;
    request.comment = "NY_Predator_v1_ModoB_Pos1";
    
    if(!OrderSend(request, result))
    {
        Print("Error abriendo posición 1 MODO B: ", GetLastError());
        return;
    }
    
    ops_hoy++;
    
    // Posición 2: Ratio 1:3 (Cierre por Trailing Stop o cierre de vela dentro de banda)
    request.tp = tp2;
    request.comment = "NY_Predator_v1_ModoB_Pos2";
    
    if(!OrderSend(request, result))
    {
        Print("Error abriendo posición 2 MODO B: ", GetLastError());
        return;
    }
    
    ops_hoy++;
}

//+------------------------------------------------------------------+
//| Verificar Doji para activar Posición 3 (MODO A)                 |
//+------------------------------------------------------------------+
void VerificarDoji()
{
    double open = iOpen(_Symbol, PERIOD_M15, 1);
    double close = iClose(_Symbol, PERIOD_M15, 1);
    double high = iHigh(_Symbol, PERIOD_M15, 1);
    double low = iLow(_Symbol, PERIOD_M15, 1);
    
    double cuerpo = MathAbs(close - open);
    double mecha_total = high - low;
    
    // Doji: cuerpo < 10% de la mecha total
    if(cuerpo < (mecha_total * 0.1))
    {
        // Abrir Posición 3
        double close_actual = iClose(_Symbol, PERIOD_M15, 0);
        double sl = close_actual - (ATR[0] * ATR_SL_Mult);
        double tp3 = close_actual + (ATR[0] * ATR_TP_Mult * 5);
        
        MqlTradeRequest request = {};
        MqlTradeResult result = {};
        
        request.action = TRADE_ACTION_DEAL;
        request.symbol = _Symbol;
        request.volume = LotSize;
        request.type = ORDER_TYPE_SELL;
        request.price = close_actual;
        request.sl = sl;
        request.tp = tp3;
        request.deviation = 10;
        request.magic = MagicNumber;
        request.comment = "NY_Predator_v1_ModoA_Pos3_Doji";
        
        if(OrderSend(request, result))
        {
            ops_hoy++;
        }
    }
}

//+------------------------------------------------------------------+
//| Trailing Stop para Posición 2 (MODO B)                          |
//+------------------------------------------------------------------+
void TrailingStop()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            if(PositionGetString(POSITION_COMMENT) == "NY_Predator_v1_ModoB_Pos2")
            {
                double close = iClose(_Symbol, PERIOD_M15, 0);
                double sl_actual = PositionGetDouble(POSITION_SL);
                double nuevo_sl = close - (ATR[0] * ATR_SL_Mult);
                
                if(nuevo_sl > sl_actual)
                {
                    MqlTradeRequest request = {};
                    MqlTradeResult result = {};
                    
                    request.action = TRADE_ACTION_SLTP;
                    request.position = PositionGetInteger(POSITION_TICKET);
                    request.sl = nuevo_sl;
                    
                    if(!OrderSend(request, result))
                    {
                        Print("Error actualizando Trailing Stop: ", GetLastError());
                    }
                }
            }
        }
    }
}
