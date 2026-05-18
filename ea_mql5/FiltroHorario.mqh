//+------------------------------------------------------------------+
//| Include: FiltroHorario.mqh                                        |
//| Obligatorio en TODOS los EAs del ecosistema BotsCuanticos        |
//| Maneja DST de Nueva York automáticamente                       |
//| 13:30 UTC invierno · 14:30 UTC verano                          |
//+------------------------------------------------------------------+
#property strict

//+------------------------------------------------------------------+
//| Detecta si NY está en horario de verano (DST)                   |
//| DST activo: segundo domingo marzo → primer domingo noviembre     |
//+------------------------------------------------------------------+
bool EsVeranoNY(datetime tiempo)
{
   MqlDateTime t;
   TimeToStruct(tiempo, t);
   int year = t.year;
   
   // Segundo domingo de marzo
   datetime marzo_start = StringToTime(StringFormat("%04d.03.01 00:00", year));
   MqlDateTime marzo;
   TimeToStruct(marzo_start, marzo);
   int domingo_marzo = (7 - marzo.day_of_week) % 7; // días hasta primer domingo
   if(domingo_marzo < 0) domingo_marzo += 7;
   datetime segundo_domingo_marzo = marzo_start + (domingo_marzo + 7) * 86400;
   
   // Primer domingo de noviembre
   datetime nov_start = StringToTime(StringFormat("%04d.11.01 00:00", year));
   MqlDateTime nov;
   TimeToStruct(nov_start, nov);
   int domingo_nov = (7 - nov.day_of_week) % 7;
   if(domingo_nov < 0) domingo_nov += 7;
   datetime primer_domingo_nov = nov_start + domingo_nov * 86400;
   
   return (tiempo >= segundo_domingo_marzo && tiempo < primer_domingo_nov);
}

//+------------------------------------------------------------------+
//| Retorna hora de apertura NY en hora del servidor MT5            |
//+------------------------------------------------------------------+
string AperturaNYServidor()
{
   datetime ahora = TimeCurrent();
   return EsVeranoNY(ahora) ? "14:30" : "13:30";
}

//+------------------------------------------------------------------+
//| Retorna hora de cierre NY en hora del servidor MT5             |
//+------------------------------------------------------------------+
string CierreNYServidor()
{
   datetime ahora = TimeCurrent();
   return EsVeranoNY(ahora) ? "21:00" : "20:00";
}

//+------------------------------------------------------------------+
//| True si estamos dentro de la sesión de Nueva York               |
//+------------------------------------------------------------------+
bool EstaEnSesionNY()
{
   string apertura = AperturaNYServidor();
   string cierre = CierreNYServidor();
   datetime ahora = TimeCurrent();
   int h = (int)TimeHour(ahora);
   int m = (int)TimeMinute(ahora);
   string ahora_str = StringFormat("%02d:%02d", h, m);
   return (ahora_str >= apertura && ahora_str <= cierre);
}

//+------------------------------------------------------------------+
//| True si estamos en ventana de apertura NY (primeros N min)      |
//+------------------------------------------------------------------+
bool EstaEnAperturaNY(int minutos_ventana = 90)
{
   string apertura_str = AperturaNYServidor();
   int h_ap, m_ap;
   StringSplit(apertura_str, ':', h_ap, m_ap);
   datetime apertura = StringToTime(StringFormat("%04d.%02d.%02d %02d:%02d",
      TimeYear(TimeCurrent()), TimeMonth(TimeCurrent()), TimeDay(TimeCurrent()),
      h_ap, m_ap));
   datetime ahora = TimeCurrent();
   return (ahora >= apertura && ahora < apertura + minutos_ventana * 60);
}

//+------------------------------------------------------------------+
//| True si estamos en sesión Asia (00:00 - 09:00 UTC)              |
//+------------------------------------------------------------------+
bool EstaEnSesionAsia()
{
   datetime ahora = TimeCurrent();
   int h = (int)TimeHour(ahora);
   return (h >= 0 && h < 9);
}

//+------------------------------------------------------------------+
//| True si estamos en sesión Europa (09:00 - apertura NY UTC)      |
//+------------------------------------------------------------------+
bool EstaEnSesionEuropa()
{
   datetime ahora = TimeCurrent();
   int h = (int)TimeHour(ahora);
   string apertura = AperturaNYServidor();
   int h_ap = (int)StringToInteger(StringSubstr(apertura, 0, 2));
   return (h >= 9 && h < h_ap);
}

//+------------------------------------------------------------------+
//| Retorna nombre de sesión actual como string                      |
//| "ASIA" | "EUROPA" | "NUEVA_YORK" | "APERTURA_NY" | "FUERA"      |
//+------------------------------------------------------------------+
string SesionActual()
{
   if(EstaEnAperturaNY())
      return "APERTURA_NY";
   if(EstaEnSesionAsia())
      return "ASIA";
   if(EstaEnSesionEuropa())
      return "EUROPA";
   if(EstaEnSesionNY())
      return "NUEVA_YORK";
   return "FUERA";
}
