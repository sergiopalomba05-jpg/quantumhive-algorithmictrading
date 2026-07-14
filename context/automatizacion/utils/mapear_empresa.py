#!/usr/bin/env python3
"""
mapear_empresa.py — QuantumHive Asset Mapper
Scanea todo el proyecto y genera QUANTUM_ESTADO_MAESTRO.md
con inventario completo de agentes, scripts, documentos y estructura.
"""

import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_DIR = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.windsurf', 'node_modules',
    '.venv', 'venv', 'env', '.env', 'deploy',
}
EXCLUDE_FILES = {
    '.env', '.gitignore', '.gitattributes', 'AGENTS.md',
    '__init__.py',
}
EXTENSIONS_INTERES = {'.py', '.ps1', '.bat', '.sh', '.md', '.sql', '.csv', '.json', '.yaml', '.yml', '.txt', '.cfg', '.conf', '.mql5', '.mq4', '.mq5'}

def walk_dir(path, level=0):
    items = []
    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return items
    for entry in entries:
        if entry.name.startswith('.') or entry.name in EXCLUDE_DIRS:
            continue
        if entry.is_dir():
            items.append({'name': entry.name, 'type': 'dir', 'children': walk_dir(entry.path, level+1), 'path': entry.path})
        else:
            ext = Path(entry.name).suffix.lower()
            if ext in EXTENSIONS_INTERES or not ext:
                items.append({'name': entry.name, 'type': 'file', 'ext': ext, 'path': entry.path, 'size': entry.stat().st_size})
    return items

def render_tree(items, indent=0, prefix=""):
    lines = []
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        line = "    " * indent + connector + item['name']
        if item['type'] == 'dir':
            lines.append(f"[DIR] {line}/")
            lines.extend(render_tree(item.get('children', []), indent + 1))
        else:
            icon = "[PY]" if item['ext'] == '.py' else ("[PS]" if item['ext'] == '.ps1' else "[  ]")
            size_kb = item['size'] / 1024
            size_str = f"({size_kb:.1f} KB)" if size_kb > 1 else ""
            lines.append(f"{icon} {line} {size_str}")
    return lines

def count_by_category(items, counts=None):
    if counts is None:
        counts = defaultdict(int)
    for item in items:
        if item['type'] == 'dir':
            counts['dirs'] += 1
            count_by_category(item.get('children', []), counts)
        else:
            ext = item.get('ext', '')
            if ext == '.py':
                counts['py'] += 1
            elif ext == '.ps1':
                counts['ps1'] += 1
            elif ext in ('.md', '.txt'):
                counts['docs'] += 1
            elif ext in ('.csv', '.json', '.yaml', '.yml'):
                counts['data'] += 1
            elif ext in ('.mql5', '.mq4', '.mq5'):
                counts['mql'] += 1
            else:
                counts['other'] += 1
    return counts

def main():
    print(f"Escaneando {PROJECT_DIR}...")

    # Walk principal (solo agentes y núcleo)
    agentes_path = PROJECT_DIR / 'automatizacion' / 'agentes'
    core_path = PROJECT_DIR / 'automatizacion' / 'agi_core'
    utils_path = PROJECT_DIR / 'automatizacion' / 'utils'
    diosmadre_path = PROJECT_DIR / 'diosmadre'

    sections = {}

    # DIOSMADRE
    if diosmadre_path.exists():
        sections['DIOSMADRE'] = walk_dir(diosmadre_path)

    # AGENTES por división
    if agentes_path.exists():
        divs = sorted([d for d in os.scandir(agentes_path) if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith('__')], key=lambda e: e.name)
        for div in divs:
            div_items = walk_dir(div.path)
            if div_items:
                sections[f'AGENTES / {div.name.upper()}'] = div_items

    # AGI CORE
    if core_path.exists():
        sections['AGI CORE'] = walk_dir(core_path)

    # UTILS
    if utils_path.exists():
        sections['UTILS'] = walk_dir(utils_path)

    # GENERAR MAESTRO
    lines = []
    lines.append("# QUANTUM_ESTADO_MAESTRO.md")
    lines.append(f"## Mapa Completo de Activos — QuantumHive Algorithmic Trading")
    lines.append(f"**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append("")

    # Stats globales
    all_items = []
    for sec_name, sec_items in sections.items():
        all_items.extend(sec_items)
    totals = count_by_category(all_items)
    total_agents = totals.get('py', 0)
    total_files = sum(v for k, v in totals.items())

    lines.append("### 📊 Resumen Global")
    lines.append(f"- **Total agentes/scripts Python:** {total_agents}")
    lines.append(f"- **Total scripts PowerShell:** {totals.get('ps1', 0)}")
    lines.append(f"- **Total documentos:** {totals.get('docs', 0)}")
    lines.append(f"- **Total archivos de datos:** {totals.get('data', 0)}")
    lines.append(f"- **Total archivos MQL:** {totals.get('mql', 0)}")
    lines.append(f"- **Total archivos escaneados:** {total_files}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for sec_name, sec_items in sections.items():
        lines.append(f"## {sec_name}")
        lines.append("")
        tree = render_tree(sec_items)
        lines.extend(tree)
        lines.append("")

    # Lista plana de agentes Python
    lines.append("---")
    lines.append("## Lista Plana de Agentes Python")
    lines.append("")

    def flatten_py(items, base_path=""):
        result = []
        for item in items:
            rel = os.path.relpath(item['path'], PROJECT_DIR)
            if item['type'] == 'dir':
                result.extend(flatten_py(item.get('children', []), item['name']))
            elif item.get('ext') == '.py' and '__' not in item['name']:
                size_kb = item['size'] / 1024
                result.append(f"- `{rel}` ({size_kb:.1f} KB)")
        return result

    for sec_name, sec_items in sections.items():
        pys = flatten_py(sec_items)
        if pys:
            lines.append(f"### {sec_name}")
            lines.extend(pys)
            lines.append("")

    output = "\n".join(lines)
    output_path = PROJECT_DIR / 'QUANTUM_ESTADO_MAESTRO.md'
    output_path.write_text(output, encoding='utf-8')
    print(f"\n✅ Generado: {output_path}")
    print(f"   {total_agents} agentes Python, {total_files} archivos totales")

if __name__ == '__main__':
    main()
