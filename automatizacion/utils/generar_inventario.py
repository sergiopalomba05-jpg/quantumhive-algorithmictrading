import os
import sys

BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'automatizacion', 'agentes')
SALIDA = os.path.join(os.path.dirname(__file__), '..', '..', 'INVENTARIO_TOTAL_QH.md')

MACROS_LEGIBLES = {
    'propfirms': 'División PropFirms',
    'fondeo': 'División Fondeo',
    'sala_inversion': 'División Sala Inversión',
    'uci': 'División UCI',
    'fabrica_bots': 'División Fábrica Bots',
    'trading': 'División Trading',
    'agi_core': 'AGI Core',
    'utils': 'Utilidades',
    'admin': 'Administración',
}

def escanear():
    """Genera INVENTARIO_TOTAL_QH.md escaneando los directorios de agentes."""
    total = 0
    with open(SALIDA, 'w', encoding='utf-8') as f:
        f.write('# INVENTARIO TOTAL QH\n\n')
        for entry in sorted(os.listdir(BASE)):
            ruta = os.path.join(BASE, entry)
            if not os.path.isdir(ruta) or entry.startswith('_') or entry.startswith('.'):
                continue
            macro = MACROS_LEGIBLES.get(entry, entry.replace('_', ' ').title())
            f.write(f'## {macro}\n\n')
            archivos = sorted([a for a in os.listdir(ruta) if a.endswith('.py') and not a.startswith('_')])
            if not archivos:
                # Buscar subdirectorios (trading/goat_btc, etc.)
                for sub in sorted(os.listdir(ruta)):
                    subruta = os.path.join(ruta, sub)
                    if os.path.isdir(subruta) and not sub.startswith('_'):
                        f.write(f'### {sub}\n\n')
                        subs = sorted([a for a in os.listdir(subruta) if a.endswith('.py') and not a.startswith('_')])
                        for a in subs:
                            f.write(f'- {sub}/{a}\n')
                            total += 1
                        f.write('\n')
            else:
                for a in archivos:
                    f.write(f'- {a}\n')
                    total += 1
                f.write('\n')
        f.write('---\n\n')
        f.write(f'**Total: {total} archivos de agente en produccion**\n')
    print(f'INVENTARIO_TOTAL_QH.md generado: {total} archivos')
    return total

if __name__ == '__main__':
    escanear()
