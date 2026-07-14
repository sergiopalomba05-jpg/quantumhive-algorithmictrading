import nbformat
import re

with open(r'C:\Users\sergio\BotsCuanticos\notebooks\kaggle_2bot_hibrido_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Dividir por los separadores de celda
pattern = r'# ══.*?CELDA \d+.*?═\n'
parts = re.split(pattern, text)

cells = []
# parts[0] es header antes de primera celda
if parts[0].strip():
    cells.append(nbformat.v4.new_markdown_cell(parts[0].strip()))

for part in parts[1:]:
    content = part.strip()
    if not content:
        continue
    # Detectar si es markdown (comentarios descriptivos sin código ejecutable)
    lines = content.split('\n')
    is_markdown = all(l.strip().startswith('#') or not l.strip() for l in lines)
    
    if is_markdown:
        # Quitar # de cada línea para markdown
        md_lines = [l.lstrip('#').strip() if l.strip().startswith('#') else l for l in lines]
        cells.append(nbformat.v4.new_markdown_cell('\n'.join(md_lines)))
    else:
        cells.append(nbformat.v4.new_code_cell(content))

nb = nbformat.v4.new_notebook(cells=cells)
nbformat.write(nb, r'C:\Users\sergio\BotsCuanticos\notebooks\KAGGLE_2BOT_HIBRIDO_v4.ipynb')
print('Notebook v4 creado: KAGGLE_2BOT_HIBRIDO_v4.ipynb')
