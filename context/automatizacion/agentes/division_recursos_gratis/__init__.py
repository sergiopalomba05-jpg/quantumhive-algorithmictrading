"""
División Recursos Gratis
========================
Gestiona recursos cloud gratuitos, VPS, GPUs, periodos de prueba y otros recursos gratuitos
para ejecutar procesos de entrenamiento distribuidos en múltiples nubes.

Agentes:
- agente_recolector_nubes: Busca nubes gratuitas y VPS
- agente_investigador_gpus: Investiga GPUs gratuitas
- agente_recolector_recursos_varios: Busca otros recursos gratuitos (APIs, datasets, herramientas)
- agente_administrador_recursos: Centraliza y gestiona toda la información de recolectores
- agente_gestor_nubes: Distribuye procesos en nubes gratuitas
- agente_reporteador: Genera informes de recursos y procesos
- api_agi_consultas: API para que AGI consulte información
"""

__version__ = "1.0.0"
