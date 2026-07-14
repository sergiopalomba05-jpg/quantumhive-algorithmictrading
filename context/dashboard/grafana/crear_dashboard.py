"""
Creador automático del Dashboard QuantumHive en Grafana
13 Macrodivisiones + métricas globales
"""

import requests
import json
from pathlib import Path

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"  # Cambiar localmente si es necesario

DASHBOARD = {
    "dashboard": {
        "id": None,
        "title": "QuantumHive — Colmena Dashboard",
        "tags": ["quantumhive", "agentes", "colmena"],
        "timezone": "America/Argentina/Buenos_Aires",
        "refresh": "30s",
        "panels": [
            # ─── FILA 1: MÉTRICAS GLOBALES ───────────────────────────
            {
                "id": 1,
                "title": "Total Agentes",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM agentes",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#C9A84C", "mode": "fixed"}}}
            },
            {
                "id": 2,
                "title": "Agentes Activos",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM agentes WHERE estado = 'activo'",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#00FF88", "mode": "fixed"}}}
            },
            {
                "id": 3,
                "title": "Agentes en Cuarentena",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM agentes WHERE estado = 'cuarentena'",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#FF4444", "mode": "fixed"}}}
            },
            {
                "id": 4,
                "title": "Alertas Activas",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM alertas WHERE resuelta = 0",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#FF4444", "mode": "fixed"}}}
            },
            {
                "id": 5,
                "title": "Eventos Hoy",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 16, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM eventos WHERE DATE(timestamp) = DATE('now')",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#C9A84C", "mode": "fixed"}}}
            },
            {
                "id": 6,
                "title": "Jobs Scheduler Activos",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 20, "y": 0},
                "targets": [{
                    "rawSQL": "SELECT COUNT(*) as value FROM agentes WHERE tiene_job = 1 AND estado = 'activo'",
                    "format": "table"
                }],
                "options": {"colorMode": "background"},
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#C9A84C", "mode": "fixed"}}}
            },

            # ─── FILA 2: TABLA AGENTES POR MACRODIVISIÓN ─────────────
            {
                "id": 10,
                "title": "🐝 Estado de la Colmena — Todos los Agentes",
                "type": "table",
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 4},
                "targets": [{
                    "rawSQL": """
                        SELECT 
                            macrodivision as 'Macro',
                            nombre as 'Agente',
                            estado as 'Estado',
                            dgcr_score as 'DGCR',
                            ultima_ejecucion as 'Última Ejecución',
                            errores_consecutivos as 'Errores'
                        FROM agentes 
                        ORDER BY macrodivision, nombre
                    """,
                    "format": "table"
                }],
                "fieldConfig": {
                    "overrides": [
                        {
                            "matcher": {"id": "byName", "options": "Estado"},
                            "properties": [{
                                "id": "custom.displayMode",
                                "value": "color-background"
                            }, {
                                "id": "mappings",
                                "value": [
                                    {"type": "value", "options": {"activo": {"color": "#00FF88", "text": "🟢 Activo"}}},
                                    {"type": "value", "options": {"inactivo": {"color": "#888888", "text": "⚪ Inactivo"}}},
                                    {"type": "value", "options": {"cuarentena": {"color": "#FF4444", "text": "🔴 Cuarentena"}}},
                                    {"type": "value", "options": {"error": {"color": "#FF4444", "text": "❌ Error"}}}
                                ]
                            }]
                        },
                        {
                            "matcher": {"id": "byName", "options": "DGCR"},
                            "properties": [{
                                "id": "custom.displayMode",
                                "value": "color-background"
                            }, {
                                "id": "thresholds",
                                "value": {
                                    "steps": [
                                        {"color": "#FF4444", "value": 0},
                                        {"color": "#FFB800", "value": 40},
                                        {"color": "#00FF88", "value": 60},
                                        {"color": "#C9A84C", "value": 90}
                                    ]
                                }
                            }]
                        }
                    ]
                }
            },

            # ─── FILA 3: AGENTES POR MACRO (BARRAS) ──────────────────
            {
                "id": 20,
                "title": "Agentes por Macrodivisión",
                "type": "barchart",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "targets": [{
                    "rawSQL": """
                        SELECT macrodivision as 'Macro', COUNT(*) as 'Total'
                        FROM agentes 
                        GROUP BY macrodivision 
                        ORDER BY macrodivision
                    """,
                    "format": "table"
                }],
                "fieldConfig": {"defaults": {"color": {"fixedColor": "#C9A84C", "mode": "fixed"}}}
            },

            # ─── FILA 3: ERRORES RECIENTES ────────────────────────────
            {
                "id": 21,
                "title": "Errores Recientes",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "targets": [{
                    "rawSQL": """
                        SELECT 
                            tipo_error as 'Tipo',
                            proceso as 'Proceso',
                            solucion_aplicada as 'Solución',
                            fecha_deteccion as 'Fecha'
                        FROM errores_procesos 
                        ORDER BY fecha_deteccion DESC 
                        LIMIT 20
                    """,
                    "format": "table"
                }]
            },

            # ─── FILA 4: ÚLTIMAS DECISIONES CEO ──────────────────────
            {
                "id": 30,
                "title": "Últimas Decisiones — CEO",
                "type": "table",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24},
                "targets": [{
                    "rawSQL": """
                        SELECT 
                            titulo as 'Decisión',
                            categoria as 'Categoría',
                            estado as 'Estado',
                            fecha as 'Fecha'
                        FROM decisiones 
                        ORDER BY fecha DESC 
                        LIMIT 15
                    """,
                    "format": "table"
                }]
            },

            # ─── FILA 5: IDEAS RECIENTES ──────────────────────────────
            {
                "id": 40,
                "title": "Ideas Recientes — Backlog",
                "type": "table",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 32},
                "targets": [{
                    "rawSQL": """
                        SELECT 
                            nombre as 'Idea',
                            categoria as 'Categoría',
                            score_viabilidad as 'Score',
                            estado as 'Estado',
                            fecha as 'Fecha'
                        FROM ideas 
                        ORDER BY score_viabilidad DESC, fecha DESC
                        LIMIT 20
                    """,
                    "format": "table"
                }]
            },

            # ─── FILA 6: EVENTOS DEL EVENT BUS ───────────────────────
            {
                "id": 50,
                "title": "Event Bus — Últimos Eventos",
                "type": "table",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 40},
                "targets": [{
                    "rawSQL": """
                        SELECT 
                            tipo as 'Evento',
                            origen as 'Origen',
                            estado as 'Estado',
                            timestamp as 'Timestamp'
                        FROM eventos 
                        ORDER BY timestamp DESC 
                        LIMIT 30
                    """,
                    "format": "table"
                }]
            },
            # ─── FILA 7: JERARQUÍA DE NODOS (NODE GRAPH) ─────────────────
            {
                "id": 60,
                "title": "Jerarquía de Nodos — Colmena",
                "type": "nodeGraph",
                "gridPos": {"h": 16, "w": 24, "x": 0, "y": 48},
                "targets": [
                    {
                        "refId": "nodes",
                        "rawSQL": """
                            SELECT CAST('root' AS TEXT) as id, CAST('QuantumHive' AS TEXT) as title, CAST('Colmena' AS TEXT) as subTitle, CAST('100' AS TEXT) as mainStat, CAST('green' AS TEXT) as color
                            UNION ALL
                            SELECT CAST(macrodivision AS TEXT) as id, CAST(macrodivision AS TEXT) as title, CAST('Macrodivisión' AS TEXT) as subTitle, CAST('' AS TEXT) as mainStat, CAST('blue' AS TEXT) as color 
                            FROM (SELECT DISTINCT macrodivision FROM agentes WHERE macrodivision IS NOT NULL)
                            UNION ALL
                            SELECT CAST(nombre AS TEXT) as id, CAST(nombre AS TEXT) as title, CAST(estado AS TEXT) as subTitle, CAST(dgcr_score AS TEXT) as mainStat,
                            CAST(CASE estado WHEN 'activo' THEN 'green' WHEN 'cuarentena' THEN 'red' ELSE 'gray' END AS TEXT) as color
                            FROM agentes WHERE nombre IS NOT NULL
                        """,
                        "format": "table"
                    },
                    {
                        "refId": "edges",
                        "rawSQL": """
                            SELECT CAST('edge_root_' || macrodivision AS TEXT) as id, CAST('root' AS TEXT) as source, CAST(macrodivision AS TEXT) as target
                            FROM (SELECT DISTINCT macrodivision FROM agentes WHERE macrodivision IS NOT NULL)
                            UNION ALL
                            SELECT CAST('edge_' || macrodivision || '_' || nombre AS TEXT) as id, CAST(macrodivision AS TEXT) as source, CAST(nombre AS TEXT) as target
                            FROM agentes WHERE macrodivision IS NOT NULL AND nombre IS NOT NULL
                        """,
                        "format": "table"
                    }
                ],
                "transformations": [
                    {
                        "id": "convertFieldType",
                        "options": {
                            "conversions": [
                                {
                                    "targetField": "id",
                                    "destinationType": "string"
                                },
                                {
                                    "targetField": "source",
                                    "destinationType": "string"
                                },
                                {
                                    "targetField": "target",
                                    "destinationType": "string"
                                }
                            ],
                            "fields": {}
                        }
                    }
                ]
            }
        ],
        "time": {"from": "now-24h", "to": "now"},
        "timepicker": {},
        "schemaVersion": 38
    },
    "overwrite": True,
    "folderId": 0
}

def crear_dashboard():
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        json=DASHBOARD
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Dashboard creado correctamente en: {GRAFANA_URL}{result.get('url', '')}")
        return True
    else:
        print(f"Error ({response.status_code}): {response.text}")
        return False

if __name__ == "__main__":
    crear_dashboard()